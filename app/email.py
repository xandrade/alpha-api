from yagmail import Connect

yag = Connect('user', 'pw')


def send_email():

    img_path = '/path/to/local/image.png'

    for name in ['andrade.antonio', 'test', ]:
        target = '{}@gmail.com'.format(name)
        yag.send(target, Subject = 'Hi ' + name, useCache = True
                Contents = ['Pre text', img_path , 'Some post text'])


if __name__ == '__main__':
    send_email()