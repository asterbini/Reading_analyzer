#   coding=utf-8

from Levenshtein import *
from Diff import diff_t
import difflib

#class Errors(object):


def entire_words(text, transcrption, k):
    error_dict = {}
    rword = text.graph[0]


    for w in transcription:
        if w != rword:
            if w == rword.precedent:
                print "Ripetizione parola"
                error_dict[rword] = (w, "Ripetizione parola")
                rword = rword.precedent
            elif w == rword.next:
                print "Salto parola"
                error_dict[rword] = (w, "Salto parola")
                rword = rword.next
            elif w == rword.precedent.up:
                print "Salto in su"
                error_dict[rword] = (w, "Salto in su")
                rword = rword.up
            elif w == rword.precedent.down:
                print "Salto in giù"
                error_dict[rword] = (w, "Salto in giù")
                rword = rword.down
        else:
            rword = rword.next
    return error_dict


def rec_alg(w, rword, description, k, i):
    if i == k:
        return None
    elif w == str(rword):
        return (description, i)
    for key, value in rword.adjacents().items():
        if w == str(value):
            return (description+" "+key, i)
    for key, value in rword.adjacents().items():
        if value != None:
            res = rec_alg(w, value, description+" "+key, k, i+1)
        if res != None:
            return res


def similar_words(text, transcription, k):
    error_list = []
    rword = text.graph[0]
    sim_list = []

    for w in transcription.split():
        if w != str(rword):
            sim_list = rec_similar(w, rword, "", k, 0, [])
            if sim_list != None:
                mdesc, mword, mperc = sim_list[0]["desc"], sim_list[0]["val"], sim_list[0]["p"]
                for t in sim_list:
                    if t["p"]<mperc:
                        mdesc, mword, mperc = t["desc"], t["val"], t["p"]
                error_list.append({"error" :"Parola simile", "rword": str(rword), "wword": w, "similar words": sim_list})
                for move in mdesc.split(" "):
                    if move == "now":
                         rword = rword
                    elif move == "next":
                        rword = rword.next
                    elif move == "up":
                        rword = rword.up
                    elif move == "precedent":
                        rword = rword.precedent
                    elif move == "down":
                        rword = rword.down
                rword = rword.next
            else:
                error_list.append({"error": "Giusta", "word": str(rword)})
                rword = rword.next

            '''
            rword_adj = rword.get_adjacents()
            for key, value in rword_adj.iteritems():
                dist = levenshteinDistance(w, value).ratio()
                if dist<min_dist:
                    closest, min_dist, fin_key = value, dist, key
            if min_dist<0.7 and min_dist!=0:
                error_dict[rword] = (w, "Parola simile "+fin_key, min_dist)
                if fin_key == "now":
                    rword = rword.next
                elif fin_key == "next":
                    rword = rword.next.next
                elif fin_key == "up":
                    rword = rword.up.next
            '''

        else:
            error_list.append({"error": "Giusta", "word": str(rword)})
            rword = rword.next
    return error_list


def rec_similar(w, rword, description, k, i, list_sim):
    if str(i) == k:
        return list_sim
    print w.encode('utf-8')+" "+str(rword)+" "+str(i)

    retlist = list_sim

    for key, value in rword.adjacents().items():
        flag = True
        perc = ratio(w.encode('utf-8'), str(value))
        if perc>0.7:
            for _w in list_sim:
                a, b, c = _w
                if str(value) == b:
                    if len(a)<len(description):
                        list_sim.remove(_w)
                    else:
                        flag = False
            if flag:
                list_sim.append({"desc": description+" "+key, "val": str(value), "p": perc})

    for key, value in rword.adjacents().items():
        if value != None:
            res = rec_similar(w, value, description+" "+key, k, i+1, list_sim)
            if res != None:
                retlist = list_sim+res
    if list_sim != retlist:
        return list_sim
    else:
        return None


#def same_startend(text, transcription):



def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def context_analyzer(text, transcription, k=1):
    #text, transcription = text.split(' '), transcription.split(' ')
    diff = list(difflib.ndiff(text, transcription))
    return diff


