def to_full_width_for_wiki(text: str) -> str:
    """
    遊戯王Wikiのページ名フォーマットに合わせるため、
    半角の英数字と一部記号（ハイフンなど）を全角に変換します。
    （例: "EM五虹の魔術師" -> "ＥＭ五虹の魔術師"）
    """
    if not text:
        return ""
    
    # 変換元の半角文字と変換先の全角文字の定義
    half_width = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-"
    full_width = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９－"
    
    trans_table = str.maketrans(half_width, full_width)
    return text.translate(trans_table)
