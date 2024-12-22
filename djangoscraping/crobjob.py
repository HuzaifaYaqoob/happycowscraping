from .scraping_main import main

def write_log(message, end='\n'):
    with open('/root/log.txt', 'a') as log_file:
        log_file.write(str(message) + end)


def scrapinghappycow():
    write_log('/////////////////////////////// cronjob working')
    for i in range(700):
        write_log(f'Working with Iteration :: {i}')
        main()