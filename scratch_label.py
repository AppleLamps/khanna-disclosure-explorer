import numpy as np

# simple 2-pass connected components (4/8-conn) without scipy
def label(bimg, connectivity=8):
    H,W = bimg.shape
    labels = np.zeros((H,W), dtype=np.int32)
    cur = 0
    from collections import deque
    if connectivity==8:
        nbrs=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    else:
        nbrs=[(-1,0),(1,0),(0,-1),(0,1)]
    for i in range(H):
        for j in range(W):
            if bimg[i,j] and labels[i,j]==0:
                cur+=1
                q=deque([(i,j)]); labels[i,j]=cur
                while q:
                    y,x=q.popleft()
                    for dy,dx in nbrs:
                        ny,nx=y+dy,x+dx
                        if 0<=ny<H and 0<=nx<W and bimg[ny,nx] and labels[ny,nx]==0:
                            labels[ny,nx]=cur; q.append((ny,nx))
    return labels, cur
