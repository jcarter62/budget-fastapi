// access cookies in javascript
// is_Admin and is_Manager
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function isAdmin() {
    return getCookie('isAdmin') === '1';
}

function isManager() {
    return getCookie('isMgr') === '1';
}

function getUsername() {
    let user = getCookie('user');
    // strip any quotes from the string
    if (user) {
        user = user.replace(/"/g, '');
        user = atob(user);
    }
    return user;
}

let userRole = '';
let userName = '';

function setSearchMgrID(mgrID) {
    // save this id to local storage as search_mgr_id
    localStorage.setItem('accounts.filter.manager', mgrID);
    localStorage.setItem('actuals.filterManager', mgrID);
    localStorage.setItem('assign.filter.manager', mgrID);
    localStorage.setItem('budgets.filterManager', mgrID);
    localStorage.setItem('home.filterManager', mgrID);
}

// create an onload function to check if the user is admin or manager and sets title accordingly
document.addEventListener('DOMContentLoaded', function() {
    let target = document.getElementById('base-title');
    if (isAdmin()) {
        target.innerText = "Admin Dashboard - Task Manager";
        userRole = 'admin';
    } else if (isManager()) {
        target.innerText = "Manager Dashboard - Task Manager";
        userRole = 'manager';
    } else {
        target.innerText = "User Dashboard - Task Manager";
        userRole = 'user';
    }

    userName = getUsername();

    //
    // enable login/logout link in base.html
    //
    let loginLink = document.getElementById('login-link');
    let logoutLink = document.getElementById('logout-link');
    if (userName) {
        loginLink.style.display = 'none';
        logoutLink.style.display = 'block';
    } else {
        loginLink.style.display = 'block';
        logoutLink.style.display = 'none';
    }


    // if user is manager, then lookup manager id, and save to local storage
    if (userRole === 'manager') {
        fetch('/api/managers/get_manager_id/' + userName, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.manager_id) {
                localStorage.setItem('manager_id', data.manager_id);
                setSearchMgrID(data.manager_id);
            }
        })
        .catch(error => {
            console.error('Error fetching manager ID:', error);
        });
    } else {
        localStorage.removeItem('manager_id');
    }

    if (userRole != 'admin') {
        let admin_controls = document.getElementsByClassName('admin-control');
        for (let i = 0; i < admin_controls.length; i++) {
            let el = admin_controls[i];
            // form controls (select, input, button) support .disabled
            if ('disabled' in el) {
                el.classList.add('disabled');          // add CSS to dim it
                el.style.pointerEvents = 'none';      // prevent clicks
                // el.disabled = true;
            } else {
                // for non-form elements (eg. <a>), make them appear/act disabled
                el.setAttribute('aria-disabled', 'true');
                el.classList.add('disabled');          // add CSS to dim it
                el.style.pointerEvents = 'none';      // prevent clicks
            }
        }
    }

});

