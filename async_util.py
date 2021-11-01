import threading

__all__ = [
    'async_exec',
]


def async_exec(f):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
        # thr.setName("方法{}".format(f.__name__))
        # thr.join()
        # print("线程id={},\n线程名称={},\n正在执行的线程列表:{},\n正在执行的线程数量={},\n当前激活线程={}".format(
        #     thr.ident, thr.getName(), threading.enumerate(), threading.active_count(), thr.isAlive)
        # )

    return wrapper
