import threading
import time

# 共享资源
current_num = 1  # 当前要打印的数字
max_num = 100  # 打印上限
turn = 1  # 当前轮到哪个线程 (1, 2, 3)
lock = threading.Lock()  # 创建锁对象


def print_number(thread_id):
    global current_num, turn

    while current_num <= max_num:
        # 1. 尝试获取锁
        with lock:
            # 2. 检查是否轮到自己
            # 如果 turn 不等于当前线程ID，说明还没轮到我，释放锁并跳过
            if turn != thread_id:
                # 注意：这里释放锁是为了让其他线程有机会获取锁来修改 turn
                continue

                # 3. 如果轮到自己，且数字未超限，执行打印
            if current_num <= max_num:
                print(f"线程{thread_id}: {current_num}")
                current_num += 1

                # 4. 关键步骤：修改 turn，通知下一个线程
                # 1 -> 2 -> 3 -> 1 ...
                if thread_id == 3:
                    turn = 1
                else:
                    turn = thread_id + 1

            # with 语句块结束，自动释放锁


# 创建三个线程
t1 = threading.Thread(target=print_number, args=(1,))
t2 = threading.Thread(target=print_number, args=(2,))
t3 = threading.Thread(target=print_number, args=(3,))

# 启动线程
t1.start()
t2.start()
t3.start()

# 等待所有线程结束
t1.join()
t2.join()
t3.join()

print("打印结束！")