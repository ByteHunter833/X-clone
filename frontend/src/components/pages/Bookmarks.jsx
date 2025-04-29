import { ArrowLeft, Search } from 'lucide-react'
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Post from '../ui/Post'

const SkeletonPost = () => (
	<div className='p-4 border-b border-gray-800 animate-pulse space-y-2'>
		<div className='flex gap-3 items-center'>
			<div className='w-10 h-10 rounded-full bg-gray-700'></div>
			<div className='flex-1 space-y-2'>
				<div className='h-4 w-1/4 bg-gray-700 rounded'></div>
				<div className='h-3 w-1/2 bg-gray-700 rounded'></div>
			</div>
		</div>
		<div className='h-4 bg-gray-700 rounded w-4/5 mt-3'></div>
		<div className='h-4 bg-gray-700 rounded w-2/3'></div>
	</div>
)

const Bookmarks = () => {
	const [bookmarks, setBookmarks] = useState([])
	const [isLoading, setIsLoading] = useState(true)
	const [searchQuery, setSearchQuery] = useState('')
	const [filteredBookmarks, setFilteredBookmarks] = useState([])
	const fetchBoookmarks = async () => {
		const userId = JSON.parse(localStorage.getItem('user'))?.user_id

		try {
			const response = await fetch(
				`http://localhost:5000/api/bookmarks?user_id=${userId}`,
				{ credentials: 'include' }
			)

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`)
			}

			const result = await response.json()

			if (result.status === 'success' && result.tweet_list) {
				setBookmarks(result.tweet_list)
				setFilteredBookmarks(result.tweet_list)
			} else {
				console.error('Error fetching bookmarks:', result.message)
			}
		} catch (error) {
			console.error('Error fetching bookmarks:', error)
		} finally {
			setIsLoading(false)
		}
	}

	useEffect(() => {
		const timer = setTimeout(() => {
			fetchBoookmarks()
		}, 500) // ⏳ небольшая задержка для плавности

		return () => clearTimeout(timer)
	}, [])

	const handleSearchChange = event => {
		const query = event.target.value.toLowerCase()
		setSearchQuery(query)
		if (query.trim() === '') {
			setFilteredBookmarks(bookmarks)
		} else {
			const filtered = bookmarks.filter(bookmark =>
				bookmark.text_content.toLowerCase().includes(query)
			)
			setFilteredBookmarks(filtered)
		}
	}
	const handleBookmarkToggle = (tweetId, isNowBookmarked) => {
		if (!isNowBookmarked) {
			setBookmarks(prev => prev.filter(post => post.id !== tweetId))
		}
	}

	return (
		<div className='min-h-screen border-x border-gray-800 w-[600px]'>
			{/* Header */}
			<div className='sticky top-0 bg-black/80 backdrop-blur-md z-10 px-4 py-3 space-y-3 border-b border-gray-800'>
				<div className='flex items-center gap-2'>
					<Link to={'/'} className='p-2 rounded-full hover:bg-gray-800/50'>
						<ArrowLeft className='w-5 h-5 text-white' />
					</Link>

					<h2 className='text-2xl font-bold text-white'>Bookmarks</h2>
				</div>

				{/* Search bar */}
				<div className='relative w-full'>
					<Search className='absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5' />
					<input
						type='text'
						placeholder='Search Bookmarks'
						value={searchQuery}
						onChange={handleSearchChange}
						className='w-full pl-10 pr-4 py-2 bg-neutral-900 text-white rounded-full border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 transition duration-200'
					/>
				</div>
			</div>

			{/* Content */}
			{isLoading ? (
				<div className='animate-fadeIn'>
					{Array(4)
						.fill(0)
						.map((_, idx) => (
							<SkeletonPost key={idx} />
						))}
				</div>
			) : bookmarks.length > 0 ? (
				<div className='animate-fadeIn space-y-1'>
					{filteredBookmarks.map(bookmark => (
						<Post
							key={bookmark.id}
							username={bookmark.user.username}
							handle={`@${bookmark.user.username}`}
							time={bookmark.created_at}
							content={bookmark.text_content}
							media={bookmark.media_content}
							avatar={bookmark.user.profile_image_url}
							id={bookmark.id}
							onBookmarkToggle={handleBookmarkToggle}
						/>
					))}
				</div>
			) : (
				<div className='flex flex-col items-center justify-center p-8 text-center animate-fadeIn'>
					<h3 className='text-3xl font-bold mb-2 text-white'>
						Save Posts for later
					</h3>
					<p className='text-gray-500 mb-4'>
						Don't let the good ones fly away! Bookmark Posts to easily find them
						again in the future.
					</p>
				</div>
			)}
		</div>
	)
}

export default Bookmarks
