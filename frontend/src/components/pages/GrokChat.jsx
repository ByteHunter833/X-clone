// components/GrokChat.jsx
import { BrainCircuit, ImageIcon, Send, Upload } from 'lucide-react'
import { useState } from 'react'
import GrokIcon from '../ui/GrokIcon'

export default function GrokChat() {
	const [input, setInput] = useState('')
	const [messages, setMessages] = useState([])
	const [loading, setLoading] = useState(false)

	const sendMessage = async () => {
		if (!input.trim()) return

		const userMessage = { role: 'user', content: input }
		const updatedMessages = [...messages, userMessage]

		setMessages(updatedMessages)
		setInput('')
		setLoading(true)

		try {
			if (!window.puter || !window.puter.ai) {
				console.error(
					"❌ Puter.js не загружен. Проверь <script src='https://js.puter.com/v2/'>"
				)
				return
			}

			const response = await window.puter.ai.chat(input.trim(), {
				model: 'x-ai/grok-3-beta',
				stream: true,
			})

			let botReply = ''
			for await (const chunk of response) {
				botReply += chunk.text
			}

			const botMessage = { role: 'assistant', content: botReply }
			setMessages(prev => [...prev, botMessage])
		} catch (error) {
			console.error('⚠️ Error contacting Grok:', error)
			setMessages(prev => [
				...prev,
				{ role: 'assistant', content: `⚠️ Error: ${error.message}` },
			])
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className='min-h-screen w-[800px] bg-black border-x border-gray-800 text-white flex flex-col items-center px-4 py-10 space-y-8'>
			{/* Logo and Title */}
			<div className='text-center'>
				<div className='text-4xl font-bold mb-2 flex items-center justify-center gap-2'>
					<GrokIcon />
					Grok
				</div>
				<div className='text-sm border-t border-gray-600 w-16 mx-auto mt-1' />
			</div>

			{/* Chat History */}
			<div
				className='max-w-2xl w-full space-y-4'
				style={{
					maxHeight: '500px',
					overflowY: 'auto',
					padding: '10px',
					borderRadius: '10px',
				}}
			>
				{messages.map((msg, i) => (
					<div
						key={i}
						className={`flex ${
							msg.role === 'user' ? 'justify-end' : 'justify-start'
						}`}
					>
						<div
							className={`p-3 rounded-xl max-w-[75%] ${
								msg.role === 'user'
									? 'bg-blue-600 text-white'
									: 'bg-gray-700 text-white'
							}`}
						>
							{msg.content}
						</div>
					</div>
				))}
				{loading && (
					<div className='flex justify-start'>
						<div className='bg-gray-700 p-3 rounded-xl italic text-gray-400 max-w-[75%]'>
							Typing...
						</div>
					</div>
				)}
			</div>

			{/* Input Area */}
			<div className='w-full max-w-2xl'>
				<div className='bg-[#1e1e1e] rounded-2xl px-4 py-3 flex flex-col gap-3 shadow-xl border border-gray-700'>
					<input
						type='text'
						placeholder='Ask anything'
						className='bg-transparent outline-none text-white placeholder-gray-400 text-base'
						value={input}
						onChange={e => setInput(e.target.value)}
						onKeyDown={e => e.key === 'Enter' && sendMessage()}
					/>
					<div className='flex items-center gap-2 flex-wrap'>
						<button className='flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 text-sm rounded-full border border-gray-600'>
							<Upload size={14} /> DeepSearch
						</button>
						<button className='flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 text-sm rounded-full border border-gray-600'>
							<BrainCircuit size={14} /> Think
						</button>
						<button className='flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 text-sm rounded-full border border-gray-600'>
							<ImageIcon size={14} /> Edit Image
						</button>
						<div className='ml-auto'>
							<button
								onClick={sendMessage}
								className='bg-gray-700 hover:bg-gray-600 p-2 rounded-full'
							>
								<Send size={16} />
							</button>
						</div>
					</div>
				</div>
			</div>

			<div className='bg-[#1a1a1a] border border-gray-700 rounded-xl px-4 py-3 text-sm max-w-2xl w-full'>
				<strong>Draw Me</strong>
				<div className='text-gray-400'>Click here to try a random style!</div>
			</div>

			<div className='grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl w-full mt-4'>
				<FeatureCard
					title='DeepSearch'
					desc='Search deeply to deliver detailed, well-reasoned answers with Grok’s rapid, agentic search.'
				/>
				<FeatureCard
					title='Think'
					desc='Solve the hardest problems in math, science, and coding with our reasoning model.'
				/>
				<FeatureCard
					title='Edit Image'
					desc='Transform your images with style transfers, edits, and more.'
				/>
			</div>
		</div>
	)
}

function FeatureCard({ title, desc }) {
	return (
		<div className='bg-[#1e1e1e] border border-gray-700 rounded-xl p-4 text-sm hover:bg-[#2a2a2a] transition'>
			<div className='font-semibold mb-1'>{title}</div>
			<div className='text-gray-400'>{desc}</div>
		</div>
	)
}

// AIzaSyA06pZPlxjAY4FZuLjd5JKc4n2nHnu7cqE
