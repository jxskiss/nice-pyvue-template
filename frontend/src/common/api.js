import makeApiModule from './api.base'

const commonApiDefs = {
  getUserProfile: '/v1/common/users/profile',
  logoutUser: '/v1/common/users/logout',
  loginUser: ['POST', '/v1/common/users/login']
}

export const commonApi = new (makeApiModule(commonApiDefs))()

const mockApiDefs = {
  getMock1Data: '/v1/mockapi/mock1',
  getMock2List: '/v1/mockapi/mock2/',
  getMock2Detail: '/v1/mockapi/mock2/:id',
  submitMock2Data: ['POST', '/v1/mockapi/mock2/']
}

const MockApiModule = makeApiModule(mockApiDefs)

export const mockApi = new MockApiModule()
