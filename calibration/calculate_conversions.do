use calibrationdata, replace

list

* left hand
reg leftweigh leftv


reg leftv leftweigh
margins , at(leftweigh=0)



*right hand
reg rightw rightv

reg rightv rightweigh
margins , at(rightweigh=0)




