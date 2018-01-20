import Cookies from 'js-cookie';
import { commonApi } from '@common/api'

const user = {
    state: {},
    actions: {
        logout (state, vm) {
            Cookies.remove('user');
            localStorage.clear();
            commonApi.logoutUser();
        }
    },
};

export default user;
