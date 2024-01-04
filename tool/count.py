# 计算token数
def count_tokens(parts):
    total_tokens = 0

    for entry in parts:
        if 'parts' in entry:
            for part in entry['parts']:
                is_in_word = False

                for char in part:
                    if ('A' <= char <= 'Z') or ('a' <= char <= 'z'):
                        is_in_word = True
                    else:
                        if is_in_word:
                            total_tokens += 1
                            is_in_word = False
                        total_tokens += 1

                if is_in_word:
                    total_tokens += 1

    return total_tokens
