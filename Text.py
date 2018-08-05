#   coding=utf-8

def nclean(string):
    result = ''
    for i in range(len(string)):
        if string[i] in punctuation:
            if string[i]=='\'':
                if i>0 and i<len(string)-1:
                    if string[i-1]!=' ' and string[i+1]!=' ':
                        result += '\''
        else:
            result += string[i]
    return result


def get_string_tlength(string, font):
    params = ImageFont.truetype(font+'.ttf', 12)
    width, height = params.getsize(string)
    return width


