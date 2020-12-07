import json
import traceback
from typing import IO
from typing import Iterable


class Meta(type):
    def __new__(mcs, name, base, attr):
        mappings = {}
        for k, v in attr.items():
            if isinstance(v, Field):
                mappings[k] = v
        for k in mappings:
            attr.pop(k)
        attr['__mappings__'] = mappings
        return type.__new__(mcs, name, base, attr)


class Field:
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value

    def __repr__(self):
        return '{}'.format(self.__class__.__name__)


class JsonItemMixin:
    """实现`dump`方法, 把一个`Item`类转化为`json`"""

    def __init__(self):
        ...

    def dump(self):
        dumping = {}
        for k, v in self.__mappings__.items():
            print('dumping: ', k, v)
            dumping[k] = v
        return dumping


class FileItemMixin:
    """实现`save`, `flush` 方法, 保存这个`Item`为一个文件"""

    def __init__(self):
        ...

    def save(self):
        ...


class Item(metaclass=Meta):
    def __init__(self):
        self.obj = {}

    def keys(self) -> Iterable:
        return self.obj.keys()

    def items(self) -> (Iterable, Iterable):
        return self.items()

    def __len__(self) -> int:
        return self.obj.__len__()

    def __setitem__(self, k, v):
        return self.obj.__setitem__(k, v)

    def __getitem__(self, k):
        return self.obj.__getitem__(k)

    def __delitem__(self, v):
        return self.obj.__delitem__(v)

    def __str__(self) -> str:
        return self.obj.__str__()


class JsonItem(Item, JsonItemMixin):
    def __init__(self):
        super(JsonItem, self).__init__()


class JsonFile(Item):

    def __init__(self, file: IO, obj: dict = None, indent=4):
        """Json与文件同步序列化
        注意不要使用此构造方法,应当使用工厂方法

        :param file: 一个文件流
        :param obj: 一个字典
        :param indent: tab的长度
        """
        super().__init__()
        if not file.writable():
            raise IOError('文件不可写<{}>'.format(file.name))
        if not file.seekable():
            raise IOError('文件不可查<{}>'.format(file.name))
        if not file.readable():
            raise IOError('文件不可读<{}>'.format(file.name))
        self.f = file
        self.obj = obj
        self.indent = indent

    @classmethod
    def from_newfile(cls, filename, mode='w', encoding='utf8'):
        f = open(filename, mode=mode, encoding=encoding)
        return cls(f, {})

    @classmethod
    def from_filename(cls, filename, mode='r+', encoding='utf8'):
        f = open(filename, mode=mode, encoding=encoding)
        c = cls(f)
        c.load(f)
        return c

    @classmethod
    def from_streaming(cls, streaming):
        c = cls(streaming, {})
        return c

    def load(self, streaming: IO):
        self.obj = json.load(streaming)

    def dump(self):
        self.f.seek(0)
        json.dump(self.obj, self.f, indent=4, ensure_ascii=False)

    def close(self):
        self.dump()
        self.f.close()


# #################################test Mapping###########################

class MyItem(Item):
    def __init__(self):
        super().__init__()

    field = Field()


class MyJsonItem(JsonItem):
    field = Field()


class Test:
    def test_json_item(self):
        mji = MyJsonItem()
        mji.dump()

    def test_mapping(self):
        it = MyItem()
        mp = it.__mappings__
        print('mp={}'.format(mp))

    def test_json2(self):
        jf2 = JsonFile.from_filename('resources/testjson2.json')
        jf2['title'] = 'changeadsfsdafdsd testjson2'
        jf2.close()

    # noinspection PyBroadException
    def start_test(self):
        method_names = [method for method in self.__dir__() if method.startswith('test')]
        for method_name in method_names:
            try:
                print('======test: [{}]======'.format(method_name))
                getattr(self, method_name)()
            except:
                print('======Exception=======')
                traceback.print_exc()


if __name__ == '__main__':
    test = Test()
    test.start_test()
