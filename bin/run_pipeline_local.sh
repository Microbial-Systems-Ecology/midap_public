#!/bin/bash

# make directory if it doesn't exist
make_dir() {
        [ ! -d $1 ] && mkdir -p $1
}

# 0) Define parameters
python set_parameters.py
source settings.sh

if [[ $DATA_TYPE == "CHAMBER" ]]
    then
        echo $PATH_FOLDER

        POSITIONS=()
        for i in $PATH_FOLDER*.$FILE_TYPE; do
        POS=$(echo $i | grep -Eo "[Pp][Oo][Ss][0-9]+")
        POSITIONS+=($POS)
        done
        POS_UNIQ=($(printf "%s\n" "${POSITIONS[@]}" | sort -u));

        for POS in "${POS_UNIQ[@]}"; do
        echo $POS

        # 1) Generate folder structure
        echo "generate folder structure"

        RAW_IM="raw_im/"
        SEG_PATH="xy1/"
        CUT_PATH="phase/"
        SEG_IM_PATH="seg_im/"
        SEG_MAT_PATH="seg/"

        # generate folders for different channels (phase, fluorescent)
        make_dir $PATH_FOLDER$POS
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/
        done

        # generate folder raw_im for raw images
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/$RAW_IM
        done

        # generate folder for tracking results
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH
        done

        # generate folder for cutout images
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH$CUT_PATH
        done

        # generate folder seg_im for segmentation images
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH
        done

        # generate folders for segmentation-mat files
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH$SEG_MAT_PATH
        done


        # 2) Copy files
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                VAR=`find $PATH_FOLDER -name *$POS*${!CH}*.tiff`
                cp $VAR $PATH_FOLDER$POS/${!CH}/
        done


        # 3) Split frames
        echo "split frames"
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                INP=$(find $PATH_FOLDER$POS/${!CH}/ -name *.tiff)
                python stack2frames.py --path $INP --pos $POS --channel /${!CH}/
        done


        # 4) Cut chambers
        echo "cut chambers"
        if [ -z "$CHANNEL_2" ] || [ -z "$CHANNEL_3" ]
                then
                python frames2cuts.py --path_ch0 $PATH_FOLDER$POS/$CHANNEL_1/$RAW_IM
                echo $PATH_FOLDER$POS$CHANNEL_1$RAW_IM
        else
                python frames2cuts.py --path_ch0 $PATH_FOLDER$POS/$CHANNEL_1/$RAW_IM --path_ch1 $PATH_FOLDER$POS/$CHANNEL_2/$RAW_IM --path_ch2 $PATH_FOLDER$POS/$CHANNEL_3/$RAW_IM
        fi


        # 5) Segmentation
        echo "segment images"
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                #if [ -z "$CHANNEL_2" ] || [ -z "$CHANNEL_3" ]
                #        then
                python main_prediction.py --path_pos $PATH_FOLDER$POS --path_channel ${!CH} --postprocessing 0
                #else
                #        python main_prediction.py --path_pos $PATH_FOLDER$POS --path_channel ${!CH} --postprocessing 0
                #fi
        done


        # 6) Conversion
        echo "run file-conversion"
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                python seg2mat.py --path_cut $PATH_FOLDER$POS/${!CH}/$SEG_PATH$CUT_PATH --path_seg $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH --path_channel $PATH_FOLDER$POS/${!CH}/
        done


        # 7) Tracking
        echo "run tracking"
        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                CH="CHANNEL_$i"
                $MATLAB_ROOT/bin/matlab -nodisplay -r "tracking_supersegger('$PATH_FOLDER$POS/${!CH}/', '$CONSTANTS' , $NEIGHBOR_FLAG, $TIME_STEP, $MIN_CELL_AGE, '$DATA_TYPE')"
                MAT_FILE=$PATH_FOLDER$POS/${!CH}/$SEG_PATH/clist.mat
                if ! test -f "$MAT_FILE"; then
                    rm -r $PATH_FOLDER$POS/${!CH}/$SEG_PATH/
                    rm $PATH_FOLDER$POS/${!CH}/CONST.mat
                    rm $PATH_FOLDER$POS/${!CH}/$RAW_IM/cropbox.mat 
                fi

        done

    done
fi

if [[ $DATA_TYPE == "WELL" ]]
    then
        # 1) Generate folder structure
        echo "generate folder structure"

        PATH_FILE_WO_EXT="${PATH_FILE%.*}"
        FILE_NAME=${PATH_FILE##*/}
        echo $PATH_FILE_WO_EXT
        echo $FILE_NAME

        RAW_IM="raw_im/"
        SEG_PATH="xy1/"
        CUT_PATH="phase/"
        SEG_IM_PATH="seg_im/"
        SEG_MAT_PATH="seg/"

        # generate folder to store the results
        make_dir $PATH_FILE_WO_EXT
        cp $PATH_FILE $PATH_FILE_WO_EXT

        # generate folders raw_im
        make_dir $PATH_FILE_WO_EXT/$RAW_IM

        # generate folders for tracking results
        make_dir $PATH_FILE_WO_EXT/$SEG_PATH

        # generate folders for cutout images
        make_dir $PATH_FILE_WO_EXT/$SEG_PATH$CUT_PATH

        # generate folders for segmentation images
        make_dir $PATH_FILE_WO_EXT/$SEG_IM_PATH

        # generate folders for segmentation-mat files
        make_dir $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH

        
        # 2) Split frames
        echo "split frames"
        python stack2frames.py --path $PATH_FILE_WO_EXT/$FILE_NAME --pos "" --channel ""
        cp $PATH_FILE_WO_EXT/$RAW_IM*.tif $PATH_FILE_WO_EXT/$SEG_PATH$CUT_PATH
        
        # 3) Segmentation
        echo "segment images"
        python main_prediction.py --path_pos $PATH_FILE_WO_EXT --path_channel "" --postprocessing 1

        # 4) Conversion
        echo "run file-conversion"
        python seg2mat.py --path_cut $PATH_FILE_WO_EXT/$SEG_PATH$CUT_PATH --path_seg $PATH_FILE_WO_EXT/$SEG_IM_PATH --path_channel $PATH_FILE_WO_EXT/

        # 5) Tracking
        echo "run tracking"
        $MATLAB_ROOT/bin/matlab -nodisplay -r "tracking_supersegger('$PATH_FILE_WO_EXT', '$CONSTANTS' , $NEIGHBOR_FLAG, $TIME_STEP, $MIN_CELL_AGE, '$DATA_TYPE')"

        MAT_FILE=$PATH_FILE_WO_EXT/$SEG_PATH/clist.mat
        if ! test -f "$MAT_FILE"; then
                rm -r $PATH_FILE_WO_EXT/$SEG_PATH/
                rm $PATH_FILE_WO_EXT/CONST.mat
                rm $PATH_FILE_WO_EXT/$RAW_IM/cropbox.mat 
        fi
fi
