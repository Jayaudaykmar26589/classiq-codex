import sys
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
IN=lambda v,a,b: int(a<=v<=b)
def I(c,h): return lambda y: int(abs(y-c)<=h)
# lower (y5=0): y in 0..31 ; upper y in 32..63 (use full y)
# x flags as functions of (x,y5); y flags as functions of y (0..63)
L_x=[lambda x:IN(x,2,26), lambda x:int(abs(x-40)<=2), lambda x:int(3<=abs(x-40)<=4), lambda x:int(5<=abs(x-40)<=6), lambda x:int(abs(x-40)==7), lambda x:int(abs(x-40)==8)]
L_y=[lambda y:IN(y,29,31), I(19,8), I(19,7), I(19,6), I(19,4), I(19,2)]
U_x=[lambda x:IN(x,2,26), lambda x:IN(x,27,61), lambda x:int(abs(x-55)<=2), lambda x:int(3<=abs(x-55)<=4), lambda x:int(abs(x-55)==5), lambda x:0]
U_y=[lambda y:IN(y,32,53), I(41,2), lambda y:I(41,6)(y)^I(41,2)(y), lambda y:I(41,5)(y)^I(41,2)(y), lambda y:I(41,4)(y)^I(41,2)(y), lambda y:0]
def X(j): return lambda x,y5: (U_x if y5 else L_x)[j](x)
def Y(j): return lambda y: (U_y[j](y) if y>=32 else L_y[j](y))
def check():
    bad=0
    for x in range(64):
        for y in range(64):
            v=0
            for j in range(6): v^=X(j)(x,y>>5)&Y(j)(y)
            bad+= v!=logo_pixel(x,y)
    return bad
if __name__=='__main__': print('mismatch',check())
