import {
	Bell,
	Bookmark,
	CircleEllipsis,
	Home,
	Mail,
	MoreHorizontal,
	Search,
	User,
} from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import GrokIcon from '../ui/GrokIcon'
import LogoutModal from '../ui/LogoutModal'
import MoreModal from '../ui/MoreModal'

const LeftSidebar = ({ openPostModal }) => {
	const [isMoreModalOpen, setIsMoreModalOpen] = useState(false)
	const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false)
	const location = useLocation()

	return (
		<div className='sticky top-0 w-72 h-screen flex flex-col p-4 border-r border-gray-800'>
			{/* Logo */}
			<Link
				to='/'
				className='mb-4 px-4 hover:bg-gray-900/50 rounded-full inline-block'
			>
				<svg
					viewBox='0 0 24 24'
					className='h-8 w-8 text-white'
					fill='currentColor'
				>
					<g>
						<path d='M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z'></path>
					</g>
				</svg>
			</Link>

			{/* Navigation */}
			<nav className='flex-1 space-y-0.5'>
				<NavItem
					to='/'
					icon={<Home className='h-7 w-7' />}
					text='Home'
					active={location.pathname === '/'}
				/>
				<NavItem
					to='/explore'
					icon={<Search className='h-7 w-7' />}
					text='Explore'
					active={location.pathname === '/explore'}
				/>
				<NavItem
					to='/notifications'
					icon={<Bell className='h-7 w-7' />}
					text='Notifications'
					active={location.pathname === '/notifications'}
				/>
				<NavItem to='/grok' icon={<GrokIcon />} text='Grok' />
				<NavItem
					to='/messages'
					icon={<Mail className='h-7 w-7' />}
					text='Messages'
					active={location.pathname === '/messages'}
				/>
				<NavItem
					to='/bookmarks'
					icon={<Bookmark className='h-7 w-7' />}
					text='Bookmarks'
					active={location.pathname === '/bookmarks'}
				/>
				<NavItem
					to='/profile'
					icon={<User className='h-7 w-7' />}
					text='Profile'
					active={location.pathname === '/profile'}
				/>
				<NavItem
					icon={<CircleEllipsis className='h-7 w-7' />}
					text='More'
					onClick={() => setIsMoreModalOpen(true)}
				/>
			</nav>

			{/* Post Button */}
			<button
				className='bg-blue-500 hover:bg-blue-600 transition-all text-white font-bold py-3.5 px-4 rounded-full w-full my-4 active:scale-95'
				onClick={openPostModal}
			>
				Post
			</button>

			{/* Profile Section */}
			<div
				className='mt-auto hover:bg-gray-900/50 rounded-full cursor-pointer transition-colors group'
				onClick={() => setIsLogoutModalOpen(true)}
			>
				<div className='flex items-center justify-between p-3'>
					<div className='flex items-center gap-3 min-w-0'>
						<div className='w-10 h-10 rounded-full bg-gray-700 flex justify-center items-center flex-shrink-0'>
							<span className='font-bold text-lg'>
								{JSON.parse(localStorage.getItem('user'))?.full_name?.[0] ||
									'U'}
							</span>
						</div>
						<div className='min-w-0 flex-1'>
							<h2 className='font-bold text-[15px] leading-5 text-white truncate'>
								{JSON.parse(localStorage.getItem('user'))?.full_name}
							</h2>
							<p className='text-gray-500 text-[13px] truncate'>
								@{JSON.parse(localStorage.getItem('user'))?.username}
							</p>
						</div>
					</div>
					<MoreHorizontal className='w-5 h-5 text-gray-500 group-hover:text-gray-400 transition-colors' />
				</div>
			</div>

			{/* Modals */}
			<MoreModal
				isOpen={isMoreModalOpen}
				onClose={() => setIsMoreModalOpen(false)}
			/>
			<LogoutModal
				isOpen={isLogoutModalOpen}
				onClose={() => setIsLogoutModalOpen(false)}
			/>
		</div>
	)
}

const NavItem = ({ icon, text, active, to, onClick }) => {
	const baseClass = `
    flex items-center gap-4 p-3 rounded-full w-full cursor-pointer
    transition-all hover:bg-gray-900/50 
    ${active ? 'font-bold' : 'font-medium'}
  `

	if (onClick) {
		return (
			<div onClick={onClick} className={baseClass}>
				{icon}
				<span className='text-xl'>{text}</span>
			</div>
		)
	}

	return to ? (
		<Link to={to} className={baseClass}>
			{icon}
			<span className='text-xl'>{text}</span>
		</Link>
	) : (
		<div className={baseClass}>
			{icon}
			<span className='text-xl'>{text}</span>
		</div>
	)
}

export default LeftSidebar
