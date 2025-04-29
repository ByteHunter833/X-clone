import { MoreHorizontal } from 'lucide-react'
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Icons from '../layout/Icons'
import PostActionModal from '../ui/PostActionModal'

const Post = ({
	username,
	handle,
	time,
	content,
	media,
	avatar,
	id,
	onBookmarkToggle,
	onLikeToggle,
	onPostDeleted,
}) => {
	const [isModalOpen, setIsModalOpen] = useState(false)
	const navigate = useNavigate()
	// Get current user from localStorage to determine if it's the user's own post
	const currentUser = JSON.parse(localStorage.getItem('user'))
	const handleClick = () => {
		navigate(`/post/${id}`)
	}

	const isOwnPost = currentUser?.username === handle.split('@')[1]

	const handleDeletePost = async postId => {
		try {
			const response = await fetch(
				`http://localhost:5000/api/tweet/${postId}`,
				{
					method: 'DELETE',
					credentials: 'include',
				}
			)

			if (!response.ok) {
				throw new Error('Failed to delete post')
			}
			onPostDeleted(postId)
			setIsModalOpen(false)
		} catch (error) {
			console.error('Error deleting post:', error)
		}
	}

	const handleEditPost = postId => {
		// Implementation for editing would go here
		console.log('Edit post:', postId)
		// Could navigate to edit page or open an edit form
	}

	return (
		<div className='border-b border-gray-800 p-4 hover:bg-gray-900/5 transition-colors cursor-pointer'>
			<div className='flex space-x-4'>
				<div className='flex-shrink-0'>
					{avatar ? (
						<img
							src={avatar}
							alt={`${username}'s avatar`}
							className='w-12 h-12 rounded-full object-cover min-w-[3rem] min-h-[3rem]'
						/>
					) : (
						<div className='w-12 h-12 min-w-[3rem] min-h-[3rem] rounded-full bg-gray-700 flex justify-center items-center'>
							<span className='font-bold text-xl'>
								{username.charAt(0).toUpperCase()}
							</span>
						</div>
					)}
				</div>

				{/* Content section */}
				<div className='flex-grow'>
					<div>
						<div className='flex justify-between'>
							<div className='flex items-center space-x-2'>
								<span className='font-bold hover:underline'>{username}</span>
								<span className='text-gray-500'>{handle}</span>
								<span className='text-gray-500'>·</span>
								<span className='text-gray-500 text-sm hover:underline'>
									{time}
								</span>
							</div>

							{/* More options button */}
							<button
								onClick={e => {
									e.stopPropagation() // Prevent triggering parent click events
									setIsModalOpen(true)
								}}
								className='p-1 rounded-full hover:bg-gray-800/50 transition-colors'
							>
								<MoreHorizontal className='w-5 h-5 text-gray-500' />
							</button>
						</div>
					</div>

					{/* Tweet content */}
					<div className='break-words whitespace-pre-wrap max-w-full overflow-hidden text-pretty'>
						<p className='mt-2 text-left text-[15px] leading-normal'>
							{content}
						</p>
					</div>

					{/* Media */}
					{media && (
						<div className='mt-3'>
							<img
								src={media}
								alt='Post media'
								className='rounded-2xl max-h-[510px] object-cover w-full border border-gray-800'
								onError={e => {
									console.error('Image failed to load:', media)
									e.target.style.display = 'none'
									e.target.parentElement.innerHTML =
										'<p class="text-gray-500">Image failed to load</p>'
								}}
							/>
						</div>
					)}

					{/* Interaction icons */}
					<div className='mt-3'>
						<Icons
							tweetId={id}
							onBookmarkToggle={onBookmarkToggle}
							onLikeToggle={onLikeToggle}
						/>
					</div>
				</div>
			</div>

			{/* Post Action Modal */}
			<PostActionModal
				isOpen={isModalOpen}
				onClose={() => setIsModalOpen(false)}
				postId={id}
				isOwnPost={isOwnPost}
				onDelete={handleDeletePost}
				onEdit={handleEditPost}
			/>
		</div>
	)
}

export default Post
