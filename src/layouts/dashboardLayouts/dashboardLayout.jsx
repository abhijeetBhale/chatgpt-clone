import { Outlet } from 'react-router-dom'
import './dashboardLayout.css'

const DashboardLayout = () => {
  return (
    <div className='dashboardLayout'>
        <div className="menu">MENU</div>
        <div className="contact"><Outlet/></div>
    </div>
  )
}

export default DashboardLayout