import { useEffect, useState } from 'react'
import {
	Navigate,
	Route,
	BrowserRouter as Router,
	Routes,
	useNavigate,
} from 'react-router-dom'
import './App.css'
import LeftSidebar from './components/layout/LeftSidebar'
import RightSidebar from './components/layout/RightSidebar'
import Bookmarks from './components/pages/Bookmarks'
import Explore from './components/pages/Explore'
import PostModal from './components/ui/PostModal'

import PostCommentPage from './components/pages/Commnets/Commnetspage'
import Messages from './components/pages/Messages'
import Notifications from './components/pages/Notifications'
import Profile from './components/pages/Profile'
import Register from './components/pages/Register'
import XHomepage from './components/pages/Xhomepage'
import GrokChat from './components/pages/GrokChat'
export const BASE_URL =
	import.meta.env.MODE === 'development' ? 'http://127.0.0.1:5000/api' : '/api'
function App() {
	return (
		<Router>
			<AppContent />
		</Router>
	)
}

function AppContent() {
	const navigate = useNavigate()
	const [isAuthenticated, setIsAuthenticated] = useState(false)
	const [isPostModalOpen, setIsPostModalOpen] = useState(false)
	const [posts, setPosts] = useState([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)

	const fetchPosts = async () => {
		try {
			const response = await fetch(`${BASE_URL}/tweets`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Accept: 'application/json',
				},
				credentials: 'include',
			})

			if (!response.ok) throw new Error('Failed to fetch posts')

			const data = await response.json()
			setTimeout(() => {
				setPosts(data.tweets || [])
				setLoading(false)
			}, 1000)
		} catch (err) {
			setError(err.message)
			setLoading(false)
		}
	}

	useEffect(() => {
		if (isAuthenticated) {
			fetchPosts()
		}
	}, [isAuthenticated])

	const handleNewPost = newPost => {
		if (newPost && newPost.id) {
			setPosts(prev => [newPost, ...prev])
		}
	}
	const handleDeletePost = async deletedPostId => {
		setPosts(prev => prev.filter(post => post.id !== deletedPostId))
	}

	useEffect(() => {
		// Check authentication on initial load and page refresh
		const checkAuth = () => {
			const userData = localStorage.getItem('user')
			if (userData) {
				try {
					const user = JSON.parse(userData)
					if (user && user.isAuthenticated) {
						setIsAuthenticated(true)
						// If on register/login page, redirect to home
						const isAuthPage = ['/register', '/login'].includes(
							window.location.pathname
						)
						if (isAuthPage) {
							navigate('/')
						}
					} else {
						handleLogout()
					}
				} catch (error) {
					handleLogout()
				}
			} else {
				handleLogout()
			}
		}

		const handleLogout = () => {
			localStorage.removeItem('user')
			setIsAuthenticated(false)
			// Only redirect to register if not already there
			if (!['/register', '/login'].includes(window.location.pathname)) {
				navigate('/register')
			}
		}

		checkAuth()
	}, [navigate])

	// Public routes that don't require authentication
	const publicRoutes = ['/register', '/login']
	const isPublicRoute = publicRoutes.includes(window.location.pathname)

	return (
		<>
			{isPublicRoute ? (
				<Routes>
					<Route path='/register' element={<Register />} />
					{/* <Route path='/login' element={<Login />} /> */}
				</Routes>
			) : (
				<div className='flex min-h-screen max-w-7xl mx-auto'>
					{isAuthenticated && (
						<LeftSidebar openPostModal={() => setIsPostModalOpen(true)} />
					)}
					<main className='flex-1'>
						<Routes>
							<Route
								path='/'
								element={
									isAuthenticated ? (
										<XHomepage
											posts={posts}
											onPostCreated={handleNewPost}
											onPostDeleted={handleDeletePost}
											loading={loading}
											error={error}
										/>
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/post/:postId'
								element={
									isAuthenticated ? (
										<PostCommentPage />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>

							<Route
								path='/profile/*' // Make user_id optional
								element={
									isAuthenticated ? (
										<Profile />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/explore/*'
								element={
									isAuthenticated ? (
										<Explore />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/notifications/*'
								element={
									isAuthenticated ? (
										<Notifications />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/messages'
								element={
									isAuthenticated ? (
										<Messages />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/bookmarks'
								element={
									isAuthenticated ? (
										<Bookmarks />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
							<Route
								path='/grok'
								element={
									isAuthenticated ? (
										<GrokChat />
									) : (
										<Navigate to='/register' replace />
									)
								}
							/>
						</Routes>
					</main>
					{isAuthenticated && <RightSidebar />}
				</div>
			)}
			<PostModal
				isOpen={isPostModalOpen}
				onClose={() => setIsPostModalOpen(false)}
				onPostCreated={handleNewPost}
			/>
		</>
	)
}

export default App
