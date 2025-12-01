# Useful commands

Encode file (-w 0 means do not wrap, create single long string)

    cat ss.txt | base64 -w 0 > ss.base64

Decode file
    
    cat ss.base64 | base64 -d

Encode single string
    
    echo -n "URL" | base64 -w 0
