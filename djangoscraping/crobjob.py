from .scraping_main import main

def write_log(message, end='\n'):
    with open('/root/log.txt', 'a') as log_file:
        log_file.write(str(message) + end)


def scrapinghappycow():
    write_log('/////////////////////////////// cronjob working')
    try:
        for i in range(700):
            write_log(f'Working with Iteration :: {i}')
            main()
    except Exception as e:
        write_log(str(e))
