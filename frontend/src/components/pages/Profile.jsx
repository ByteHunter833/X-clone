import { motion } from 'framer-motion'
import { ArrowLeft, Camera, X } from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'
import {
	Link,
	NavLink,
	Route,
	Routes,
	useLocation,
	useNavigate,
	useParams,
} from 'react-router-dom'
import Post from '../ui/Post'

const fadeIn = {
	hidden: { opacity: 0, y: 20 },
	visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const tabContentVariants = {
	hidden: { opacity: 0 },
	visible: { opacity: 1, transition: { duration: 0.4 } },
}

const modalVariants = {
	hidden: { opacity: 0 },
	visible: { opacity: 1, transition: { duration: 0.2 } },
}

const Profile = () => {
	const location = useLocation()
	const navigate = useNavigate()
	const { user_id } = useParams()
	const [userData, setUserData] = useState(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)
	const [activeTab, setActiveTab] = useState(0)
	const [isTabContentLoading, setIsTabContentLoading] = useState(false)
	const [isEditModalOpen, setIsEditModalOpen] = useState(false)
	const [formData, setFormData] = useState({
		name: '',
		bio: '',
	})
	const [avatarPreview, setAvatarPreview] = useState(null)
	const [bannerPreview, setBannerPreview] = useState(null)
	const avatarInputRef = useRef(null)
	const bannerInputRef = useRef(null)

	const tabs = [
		{ name: 'Posts', path: '' },
		{ name: 'Replies', path: 'replies' },
		{ name: 'Media', path: 'media' },
		{ name: 'Likes', path: 'likes' },
	]

	useEffect(() => {
		if (location.pathname === '/profile') {
			navigate('/profile/')
		}

		const path = location.pathname.split('/').pop()
		const tabIndex = tabs.findIndex(
			tab =>
				(tab.path === '' && (path === 'profile' || path === '')) ||
				path === tab.path
		)

		if (tabIndex >= 0 && tabIndex !== activeTab) {
			setIsTabContentLoading(true)
			setActiveTab(tabIndex)
			setTimeout(() => {
				setIsTabContentLoading(false)
			}, 300)
		}
	}, [location, navigate, tabs, activeTab])

	useEffect(() => {
		const fetchProfile = async () => {
			try {
				const targetUserId =
					user_id || JSON.parse(localStorage.getItem('user'))?.user_id
				if (!targetUserId) throw new Error('No user ID available')

				const response = await fetch(
					`http://localhost:5000/api/profile/${targetUserId}`,
					{
						method: 'GET',
						credentials: 'include',
					}
				)

				if (!response.ok) throw new Error('Failed to fetch profile')

				const data = await response.json()
				if (data.status === 'success') {
					setUserData(data.user)
					setFormData({
						name: data.user.full_name || '',
						bio: data.user.bio || '',
					})
				} else {
					throw new Error(data.message || 'Failed to fetch profile')
				}
			} catch (err) {
				console.error('Profile fetch error:', err)
				setError(err.message)
			} finally {
				setLoading(false)
			}
		}

		fetchProfile()
	}, [user_id])

	const handleEditProfile = () => {
		setIsEditModalOpen(true)
	}

	const handleCloseModal = () => {
		setIsEditModalOpen(false)
		setAvatarPreview(null)
		setBannerPreview(null)
	}

	const handleInputChange = e => {
		const { name, value } = e.target
		setFormData({
			...formData,
			[name]: value,
		})
	}

	const handleAvatarClick = () => {
		avatarInputRef.current.click()
	}

	const handleBannerClick = () => {
		bannerInputRef.current.click()
	}

	const handleAvatarChange = async e => {
		const file = e.target.files[0]
		if (!file) return

		// Validate file type and size
		const validTypes = ['image/jpeg', 'image/png', 'image/gif']
		if (!validTypes.includes(file.type)) {
			alert('Please upload a JPEG, PNG, or GIF image.')
			return
		}
		if (file.size > 5 * 1024 * 1024) {
			alert('Image size must be less than 5MB.')
			return
		}

		// Set preview
		const reader = new FileReader()
		reader.onloadend = () => {
			setAvatarPreview(reader.result)
		}
		reader.readAsDataURL(file)
	}

	const handleBannerChange = async e => {
		const file = e.target.files[0]
		if (!file) return

		// Validate file type and size
		const validTypes = ['image/jpeg', 'image/png', 'image/gif']
		if (!validTypes.includes(file.type)) {
			alert('Please upload a JPEG, PNG, or GIF image.')
			return
		}
		if (file.size > 10 * 1024 * 1024) {
			alert('Image size must be less than 10MB.')
			return
		}

		// Set preview
		const reader = new FileReader()
		reader.onloadend = () => {
			setBannerPreview(reader.result)
		}
		reader.readAsDataURL(file)
	}

	const handleSaveProfile = async () => {
		try {
			const targetUserId = JSON.parse(localStorage.getItem('user'))?.user_id
			if (!targetUserId) throw new Error('No user ID available')

			// Update profile data
			const profileFormData = new FormData()
			profileFormData.append('full_name', formData.name)
			profileFormData.append('bio', formData.bio)

			if (avatarInputRef.current.files[0]) {
				profileFormData.append(
					'profile_image_url',
					avatarInputRef.current.files[0]
				)
			}
			if (bannerInputRef.current.files[0]) {
				profileFormData.append(
					'banner_image_url',
					bannerInputRef.current.files[0]
				)
			}
			for (let pair of profileFormData.entries()) {
				console.log(pair[0] + ': ' + pair[1])
			}
			const response = await fetch(
				`http://localhost:5000/api/edit/profile/${targetUserId}`,
				{
					method: 'PUT',
					credentials: 'include',
					body: profileFormData,
				}
			)
			const data = await response.json()
			console.log(data)
			if (!response.ok) throw new Error('Failed to update profile')

			if (data.status === 'success') {
				setUserData({
					...userData,
					full_name: formData.name,
					bio: formData.bio,
					profile_image_url:
						data.user.profile_image_url || userData.profile_image_url,
					banner_image_url:
						data.user.banner_image_url || userData.banner_image_url,
				})
				setIsEditModalOpen(false)
				setAvatarPreview(null)
				setBannerPreview(null)
			} else {
				throw new Error(data.message || 'Failed to update profile')
			}
		} catch (err) {
			console.error('Profile update error:', err)
			alert('Failed to update profile: ' + err.message)
		}
	}

	if (loading || error || !userData) {
		const message = error
			? error
			: !userData
			? 'Profile not found'
			: 'Loading profile...'
		const color = error ? 'text-red-500' : 'text-gray-500'

		return (
			<div className='min-h-screen flex items-center justify-center bg-black border-x border-gray-800 w-[600px] mx-auto'>
				<p className={`${color} text-lg`}>{message}</p>
			</div>
		)
	}

	return (
		<motion.div
			initial='hidden'
			animate='visible'
			variants={fadeIn}
			className='min-h-screen border-x border-gray-800 w-[600px] mx-auto bg-black relative'
		>
			{/* Header */}
			<div className='sticky top-0 bg-black/80 backdrop-blur-md z-10 px-4 py-3 flex items-center border-b border-gray-800'>
				<Link
					to='/'
					className='p-2 rounded-full mr-6 hover:bg-gray-800 transition-colors'
				>
					<ArrowLeft className='w-5 h-5 text-white' />
				</Link>
				<div>
					<h2 className='font-bold text-xl text-white'>{userData.full_name}</h2>
					<p className='text-gray-500 text-sm text-left'>
						{userData.post_count || 0} posts
					</p>
				</div>
			</div>

			{/* Banner */}
			<div className='h-32'>
				{userData.banner_image_url || bannerPreview ? (
					<img
						src={bannerPreview || userData.banner_image_url}
						alt='Banner'
						className='w-full h-full object-cover'
					/>
				) : (
					<div className='h-full bg-gradient-to-br from-gray-800 to-gray-700'></div>
				)}
			</div>

			{/* Avatar + Edit Button */}
			<div className='px-4 pb-3 flex justify-between items-start relative'>
				<div className='absolute -top-12'>
					<div className='w-24 h-24 rounded-full border-4 border-black bg-gray-700 overflow-hidden flex justify-center items-center'>
						{avatarPreview || userData.profile_image_url ? (
							<img
								src={avatarPreview || userData.profile_image_url}
								alt='Avatar'
								className='w-full h-full object-cover'
							/>
						) : (
							<span className='font-bold text-4xl text-gray-300'>
								{userData.full_name?.charAt(0).toUpperCase()}
							</span>
						)}
					</div>
				</div>
				<div className='ml-auto mt-2'>
					<button
						className='px-4 py-1.5 rounded-full border border-gray-600 font-semibold text-sm text-white hover:bg-gray-900 transition-colors'
						onClick={handleEditProfile}
					>
						Edit profile
					</button>
				</div>
			</div>

			{/* Info */}
			<div className='px-4 mt-6 mb-4 text-white'>
				<h2 className='font-bold text-xl text-left'>{userData.full_name}</h2>
				<p className='text-gray-500 text-left'>@{userData.username}</p>

				{userData.bio && (
					<p className='mt-3 text-left text-gray-300'>{userData.bio}</p>
				)}

				{userData.location && (
					<p className='mt-2 text-left text-gray-500'>
						<span className='mr-1'>📍</span>
						{userData.location}
					</p>
				)}

				<div className='flex gap-4 mt-3 text-sm text-gray-400'>
					<span className='hover:underline cursor-pointer transition-colors'>
						<strong className='text-white'>
							{userData.following_count || 0}
						</strong>{' '}
						Following
					</span>
					<span className='hover:underline cursor-pointer transition-colors'>
						<strong className='text-white'>
							{userData.follower_count || 0}
						</strong>{' '}
						Followers
					</span>
				</div>
			</div>

			{/* Tabs */}
			<div className='flex border-b border-gray-800 sticky top-14 bg-black/80 backdrop-blur-md z-10'>
				{tabs.map((tab, index) => (
					<NavLink
						key={tab.name}
						to={`/profile${tab.path ? `/${tab.path}` : ''}`}
						end={tab.path === ''}
						className={({ isActive }) => `
              w-[150px] py-3 text-center font-medium text-sm
              cursor-pointer transition-colors hover:bg-gray-900/50
              border-b-4 ${
								isActive ||
								(tab.path === '' && location.pathname === '/profile')
									? 'border-blue-500 text-white'
									: 'border-transparent text-gray-400 hover:text-gray-300'
							}
            `}
					>
						{tab.name}
					</NavLink>
				))}
			</div>

			{/* Tab Content */}
			{isTabContentLoading ? (
				<div className='p-8 flex justify-center'>
					<p className='text-gray-500'>Loading content...</p>
				</div>
			) : (
				<motion.div
					key={location.pathname}
					initial='hidden'
					animate='visible'
					variants={tabContentVariants}
					className='divide-y divide-gray-800'
				>
					<Routes>
						<Route index element={<Posts />} />
						<Route path='replies' element={<Replies />} />
						<Route path='media' element={<Media />} />
						<Route path='likes' element={<Likes />} />
					</Routes>
				</motion.div>
			)}

			{/* Edit Profile Modal */}
			{isEditModalOpen && (
				<div className='fixed inset-0 bg-black/70 flex items-center justify-center z-50'>
					<motion.div
						initial='hidden'
						animate='visible'
						variants={modalVariants}
						className='bg-black w-[600px] rounded-2xl border border-gray-800 shadow-xl'
					>
						<div className='flex items-center justify-between p-4 border-b border-gray-800'>
							<div className='flex items-center gap-8'>
								<button
									onClick={handleCloseModal}
									className='p-2 rounded-full hover:bg-gray-800 transition-colors'
								>
									<X className='w-5 h-5 text-white' />
								</button>
								<h2 className='text-xl font-bold text-white'>Edit profile</h2>
							</div>
							<button
								onClick={handleSaveProfile}
								className='px-4 py-1.5 bg-white text-black rounded-full font-bold text-sm hover:bg-gray-200 transition-colors'
							>
								Save
							</button>
						</div>

						<div className='relative'>
							{/* Banner */}
							<div
								className='h-48 relative cursor-pointer'
								onClick={handleBannerClick}
							>
								{bannerPreview || userData.banner_image_url ? (
									<img
										src={bannerPreview || userData.banner_image_url}
										alt='Banner'
										className='w-full h-full object-cover'
									/>
								) : (
									<div className='h-full bg-gradient-to-br from-gray-800 to-gray-700'></div>
								)}
								<div className='absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 hover:opacity-100 transition-opacity'>
									<Camera className='w-6 h-6 text-white' />
								</div>
							</div>
							<input
								type='file'
								accept='image/jpeg,image/png,image/gif'
								ref={bannerInputRef}
								onChange={handleBannerChange}
								className='hidden'
							/>

							{/* Avatar */}
							<div
								className='absolute left-4 -bottom-12 cursor-pointer'
								onClick={handleAvatarClick}
							>
								<div className='w-24 h-24 rounded-full border-4 border-black bg-gray-700 overflow-hidden flex justify-center items-center relative'>
									{avatarPreview || userData.profile_image_url ? (
										<img
											src={avatarPreview || userData.profile_image_url}
											alt='Avatar'
											className='w-full h-full object-cover'
										/>
									) : (
										<span className='font-bold text-4xl text-gray-300'>
											{userData.full_name?.charAt(0).toUpperCase()}
										</span>
									)}
									<div className='absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 hover:opacity-100 transition-opacity'>
										<Camera className='w-6 h-6 text-white' />
									</div>
								</div>
							</div>
							<input
								type='file'
								accept='image/jpeg,image/png,image/gif'
								ref={avatarInputRef}
								onChange={handleAvatarChange}
								className='hidden'
							/>
						</div>

						<div className='p-4 mt-16 space-y-4'>
							{/* Name Input */}
							<div className='rounded-md border border-gray-700 bg-black overflow-hidden focus-within:border-blue-500 transition-colors'>
								<label className='block px-3 pt-2 text-xs text-gray-500'>
									Name
								</label>
								<input
									type='text'
									name='name'
									value={formData.name}
									onChange={handleInputChange}
									maxLength={50}
									className='w-full px-3 pb-2 bg-transparent text-white text-lg focus:outline-none'
								/>
							</div>

							{/* Bio Input */}
							<div className='rounded-md border border-gray-700 bg-black overflow-hidden focus-within:border-blue-500 transition-colors'>
								<label className='block px-3 pt-2 text-xs text-gray-500'>
									Bio
								</label>
								<textarea
									name='bio'
									value={formData.bio}
									onChange={handleInputChange}
									maxLength={160}
									className='w-full px-3 pb-2 bg-transparent text-white resize-none h-20 focus:outline-none'
								/>
							</div>

							{/* Location Input */}
						</div>
					</motion.div>
				</div>
			)}
		</motion.div>
	)
}

const EmptyState = ({ message }) => (
	<div className='flex flex-col items-center justify-center py-16 px-4 text-center'>
		<p className='text-xl font-medium text-gray-500'>{message}</p>
		<p className='text-sm mt-2 text-gray-600'>
			When they post, you'll see them here
		</p>
	</div>
)

const Posts = () => {
	const [posts, setPosts] = useState([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)
	const user_id = JSON.parse(localStorage.getItem('user'))?.user_id

	useEffect(() => {
		const fetchPosts = async () => {
			try {
				if (!user_id) throw new Error('No user ID available')

				const resp = await fetch(
					`http://localhost:5000/api/tweets/${user_id}`,
					{
						method: 'GET',
						headers: {
							'Content-Type': 'application/json',
							Accept: 'application/json',
						},
						credentials: 'include',
					}
				)
				if (!resp.ok) {
					throw new Error('Failed to fetch posts')
				}
				const data = await resp.json()
				if (data.status === 'success') {
					setPosts(data.tweets)
				} else {
					throw new Error(data.message || 'Failed to fetch posts')
				}
			} catch (err) {
				console.error(err)
				setError('Failed to fetch posts')
			} finally {
				setLoading(false)
			}
		}

		fetchPosts()
	}, [user_id])

	return (
		<div className='divide-y divide-gray-800'>
			{loading && (
				<p className='text-gray-500 p-4 text-center'>Loading posts...</p>
			)}
			{posts.length === 0 && <EmptyState message='No posts yet' />}
			{!loading && !error && posts.length > 0 && (
				<div>
					{posts.map(post => (
						<Post
							key={post.id}
							username={post.user.username}
							// username={`@${post.user.username}`}
							content={post.text_content}
							time={post.created_at}
							handle={`@${post.user.username}`}
							avatar={post.user.profile_image_url}
							media={post.media_content}
							id={post.id}
						/>
					))}
				</div>
			)}
		</div>
	)
}

const Replies = () => {
	const [replies, setReplies] = useState([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)
	const user_id = JSON.parse(localStorage.getItem('user'))?.user_id

	useEffect(() => {
		const fetchReplies = async () => {
			try {
				if (!user_id) throw new Error('No user ID available')

				const resp = await fetch(
					`http://localhost:5000/api/replies/${user_id}`,
					{
						method: 'GET',
						headers: {
							'Content-Type': 'application/json',
							Accept: 'application/json',
						},
						credentials: 'include',
					}
				)

				if (!resp.ok) {
					throw new Error('Failed to fetch replies')
				}

				const data = await resp.json()
				if (data.status === 'success') {
					setReplies(data.replies || [])
				} else {
					throw new Error(data.message || 'Failed to fetch replies')
				}
			} catch (err) {
				console.error('Error fetching replies:', err)
				setError('Failed to fetch replies')
			} finally {
				setLoading(false)
			}
		}

		fetchReplies()
	}, [user_id])

	return (
		<div className='divide-y divide-gray-800'>
			{loading && (
				<p className='text-gray-500 p-4 text-center'>Loading replies...</p>
			)}
			{error && <p className='text-red-500 p-4 text-center'>{error}</p>}
			{!loading && !error && replies.length === 0 && (
				<EmptyState message='No replies yet' />
			)}
			{!loading && !error && replies.length > 0 && (
				<div>
					{replies.map(reply => (
						<div key={reply.id} className='border-b border-gray-800'>
							{/* Original Tweet */}
							<Post
								key={`original-${reply.original_tweet.id}`}
								id={reply.original_tweet.id}
								username={reply.original_tweet.user.username}
								handle={`@${reply.original_tweet.user.username}`}
								time={reply.original_tweet.created_at}
								content={reply.original_tweet.text_content}
								media={reply.original_tweet.media_content}
								avatar={reply.original_tweet.user.profile_image_url}
							/>

							{/* Reply */}
							<div className='pl-8 border-l border-gray-800 ml-6'>
								<div className='flex items-center space-x-2 px-4 py-2 text-gray-500'>
									<span>Replying to @{reply.original_tweet.user.username}</span>
								</div>
								<Post
									key={`reply-${reply.id}`}
									id={reply.id}
									username={reply.user.username}
									handle={`@${reply.user.username}`}
									time={reply.created_at}
									content={reply.text_content}
									media={reply.media_content}
									avatar={reply.user.profile_image_url}
								/>
							</div>
						</div>
					))}
				</div>
			)}
		</div>
	)
}

const Media = () => <EmptyState message='No media yet' />

const Likes = () => {
	const [likes, setLikes] = useState([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)
	const user_id = JSON.parse(localStorage.getItem('user'))?.user_id
	const handleLikeToggle = (postId, isNowLiked) => {
		if (!isNowLiked) {
			setLikes(prev => prev.filter(post => post.id !== postId))
		}
	}
	useEffect(() => {
		const fetchLikes = async () => {
			try {
				const resp = await fetch(`http://localhost:5000/api/likes/${user_id}`, {
					method: 'GET',
					headers: {
						'Content-Type': 'application/json',
						Accept: 'application/json',
					},
					credentials: 'include',
				})

				if (!resp.ok) {
					throw new Error('Failed to fetch likes')
				}

				const data = await resp.json()
				if (data.status === 'success') {
					setLikes(data.liked_tweets || [])
				} else {
					throw new Error(data.message || 'Failed to fetch likes')
				}
			} catch (err) {
				console.error('Error fetching likes:', err)
				setError('Failed to fetch likes')
			} finally {
				setLoading(false)
			}
		}

		if (user_id) {
			fetchLikes()
		} else {
			setLoading(false)
		}
	}, [user_id])

	return (
		<div className='divide-y divide-gray-800'>
			{loading && (
				<p className='text-gray-500 p-4 text-center'>Loading likes...</p>
			)}
			{error && <p className='text-red-500 p-4 text-center'>{error}</p>}
			{!loading && !error && likes.length === 0 && (
				<EmptyState message='No likes yet' />
			)}
			{!loading && !error && likes.length > 0 && (
				<div>
					{likes.map(like => (
						<Post
							key={like.id}
							username={like.user.username}
							content={like.text_content}
							time={like.created_at}
							handle={like.user.username}
							avatar={like.user.profile_image_url}
							media={like.media_content}
							id={like.id}
							onLikeToggle={handleLikeToggle}
						/>
					))}
				</div>
			)}
		</div>
	)
}

export default Profile
