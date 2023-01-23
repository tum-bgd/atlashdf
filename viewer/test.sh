#!/bin/bash


function validation_data_hashes(){
cat <<EOF
fa33835df33b2d4e14954e75ae6a0a35 oberbayern-water-triangles.h5
EOF
}

function check_hash()
{
    grep "$1" <(validation_data_hashes)
    return #!
}


echo "Checking whether your files are known"
for f in *.h5; do
    echo "Computing MD5 of $f"
    MD5=$(md5sum "$f");
    HASH=$(echo $MD5 |cut -d" " -f 1)
    echo "Hash $HASH"
    if check_hash "$HASH"; then
	echo "Good file"
    else
	echo "Unknown file. Expect Problems"
    fi
    
done
