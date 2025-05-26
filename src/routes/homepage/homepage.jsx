import { Link } from 'react-router-dom'
import './homepage.css'

const Homepage = () => {
  return (
    <div className='homepage'>
      <Link to="/dashboard" className='signInButton'>Dashboard</Link>
    </div>
  )
}

export default Homepage