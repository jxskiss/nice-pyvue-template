import makeApiModule from './api.base'

const commonApiDefs = {
  getUserProfile: '/api/v1/common/users/profile',
  logoutUser: '/api/v1/common/users/logout',
  loginUser: ['POST', '/api/v1/common/users/login']
}

export const commonApi = new (makeApiModule(commonApiDefs))()

const mockApiDefs = {
  getMock1Data: '/api/v1/mockapi/mock1',
  getMock2List: '/api/v1/mockapi/mock2/',
  getMock2Detail: '/api/v1/mockapi/mock2/:id',
  submitMock2Data: ['POST', '/api/v1/mockapi/mock2/']
}

const MockApiModule = makeApiModule(mockApiDefs)

export const mockApi = new MockApiModule()
