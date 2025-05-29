// import { Link } from 'react-router-dom'
// import './chatList.css'

// const ChatList = () => {
//   return (
//     <div className='chatList'>
//         <span className='title'>DashBoard</span>
//         <Link to="/dashboard">Create a New Chat</Link>
//         <Link to="/">Explore Boost AI</Link>
//         <Link to="/">Contact</Link>
//         <hr />
//         <span className='title'>Recent Chats</span>
//         <div className="list">
//             <Link to="/">My chat 1</Link>            
//             <Link to="/">My chat 1</Link>            
//             <Link to="/">My chat 1</Link>            
//             <Link to="/">My chat 1</Link>            
//             <Link to="/">My chat 1</Link>            
//         </div>
//         <hr />
//         <div className="upgrade">
//             <img src="/logo.png" alt="" />
//             <div className="text">
//                 <span>Upgrade to Boost AI Pro Version</span>
//                 <span>Get Unlimited Prompts & Latest Features</span>
//             </div>
//         </div>
//     </div>
//   )
// }

// export default ChatList

import { Link } from "react-router-dom";
import "./chatList.css";

const ChatList = () => {
    return (
        <div className="chatList">
            <span className="title">DASHBOARD</span>
            <Link to="/dashboard">Create a new Chat</Link>
            <Link to="/">Explore Lama AI</Link>
            <Link to="/">Contact</Link>
            <hr />
            <span className="title">RECENT CHATS</span>
            <div className="list">
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>                      
                <Link to="/">My chat 1</Link>                    
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
                <Link to="/">My chat 1</Link>
            </div>
            <hr />
            <div className="upgrade">
                <img src="/logo.png" alt="" />
                <div className="texts">
                    <span>Upgrade to Boost AI Pro</span>
                    <span>Get unlimited access to all features</span>
                </div>
            </div>
        </div>
    );
};

export default ChatList;