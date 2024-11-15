// Header.js
import React from 'react';
import { NavLink } from 'react-router-dom';
import "./Header.css";
import hacks_ai from "../../assets/hacks_ai.png";

const Header = () => {
    return (
        <nav className="navbar navbar-expand-md bg-body-tertiary">
            <div className="container-fluid">
                <button
                    className="navbar-toggler ml-auto"
                    data-bs-toggle="collapse"
                    data-bs-target="#navbarSupportedContent"
                    aria-controls="navbarSupportedContent"
                    aria-expanded="false"
                    type="button"
                >
                    <span className="navbar-toggler-icon"></span>
                </button>
                <div className="collapse navbar-collapse" id="navbarSupportedContent">
                    <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                        <li className="nav-item">
                            <NavLink
                                to="/"
                                end
                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''} fs`}
                            >
                                Главная
                            </NavLink>
                        </li>

                        <li className="nav-item">
                            <NavLink
                                to="/result"
                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                            >
                                Результат
                            </NavLink>
                        </li>

                        <li className="nav-item">
                            <NavLink
                                to="/info"
                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                            >
                                Команда
                            </NavLink>
                        </li>
                    </ul>
                </div>
                <img src={hacks_ai} height="30px" alt="Logo" className="navbar-img"/>
            </div>
        </nav>
    );
};

export default Header;
