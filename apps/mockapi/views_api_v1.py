# -*- coding:utf-8 -*-
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from utils.django.api import api_view
from utils.decorators import mock

# Create your views here.


@api_view(methods=('GET',))
@mock(key='mock1', file='mock_data.json', ttl=3600)
def mock1(request):
    """
    @api {GET} /v1/mockapi/mock1 测试数据接口
    @apiVersion 1.0.0
    @apiName DataMock1
    @apiGroup V1-Mock

    @apiDescription Mock 数据接口示例。

Mock 数据接口主要用来在后端 API 实现完成之前，可以快速给到前端数据，
通过使用支持注释的 JSON 文件作为 Mock 数据定义，接口定义也可以跟 Mock 数据写在一起，
方便前后端协作开发和开发维护。

前端和后端开发都可以已自己熟悉的方式编写 API 文档和 Mock 数据，并且只需要写一次。
写在 JSON 文件中的 Mock 数据，除了可以使用 `mock` 装饰器输出之外，在开发启动初期，
也可以直接由前端借助 JSMin `import` 到代码中使用。

希望可以给前后端的协作开发带来如丝般的顺滑体验，你懂的。

使用 Python 的 Docstring 编写文档，这种段落文本的缩进问题可能是会逼死强迫症患者的。
有时候觉得 Python 也不是完全热爱生命的，嗯。

    @apiSuccess {String} code 请求状态
    @apiSuccess {String} [message] 错误消息
    @apiSuccess {Object} [data] 返回数据

    """
    raise NotImplementedError()


@method_decorator([
    api_view(methods=('GET', 'POST'), login_required=False),
    csrf_exempt
], name='dispatch')
class Mock2View(View):
    """
    The APIs definition can also be written within the mock json file.
    See file "mock_data.json" for examples.

    """

    # The param file is optional, if absent, files "mock_data.json" and
    # "mock.json" will be searched
    @mock(key='mock2_get')
    def get(self, request, some_id=None):
        raise NotImplementedError()

    # You can also raise mock.PleaseMockMe to make the mock decorator
    # intercept the response.
    # When using PleaseMockMe, a different key can be specified optionally.
    @mock(key='mock2_post')
    def post(self, request):
        data = []
        if not data:
            raise mock.PleaseMockMe('mock2_post_alternative')
        return data
