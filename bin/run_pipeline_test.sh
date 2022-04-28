#!/bin/bash

# make directory if it doesn't exist
make_dir() {
        [ ! -d $1 ] && mkdir -p $1
}

# delete folder if it exists
delete_folder() {
        [ -e $1 ] && rm -r $1
}

# 0) Define parameters
python set_parameters.py
source settings.sh

if [[ $DATA_TYPE == "FAMILY_MACHINE" ]]
    then
        echo $PATH_FOLDER
        
        # extract different positions from one dataset
        POSITIONS=()
        for i in $PATH_FOLDER*.$FILE_TYPE; do
                POS=$(echo $i | grep -Eo "${POS_IDENTIFIER}[0-9]+")
                POSITIONS+=($POS)
        done
        POS_UNIQ=($(printf "%s\n" "${POSITIONS[@]}" | sort -u));

        for POS in "${POS_UNIQ[@]}"; do
                echo $POS

                # restrict frames for each position separately
                if  [ $POS != "${POS_UNIQ[0]}" ]
                then
                        echo $POS
                        python restrict_frames.py                        
                        source settings.sh
                fi

                # specify different folders needed for segmentation and tracking
                RAW_IM="raw_im/"
                #SEG_PATH="xy1/"
                #CUT_PATH="phase/"
                CUT_PATH="cut_im/"
                SEG_IM_PATH="seg_im/"
                #SEG_MAT_PATH="seg/"
                SEG_IM_TRACK_PATH="input_ilastik_tracking/"
		        TRACK_OUT_PATH="track_output/"

                # 1) Generate folder structure
                if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                then
                        echo "generate folder structure"

                        # Delete results folder for this position in case it already exists.
                        # In this way the segmentation can be rerun
                        delete_folder $PATH_FOLDER$POS

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

                        # # generate folder for tracking results
                        # for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                        #         CH="CHANNEL_$i"
                        #         make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH
                        # done

                        # generate folder for cutout images
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                #make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH$CUT_PATH
                                make_dir $PATH_FOLDER$POS/${!CH}/$CUT_PATH
                        done

                        # generate folder seg_im for segmentation images
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH
                        done

                        # generate folder seg_im_track for stacks of segmentation images for tracking
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                make_dir $PATH_FOLDER$POS/${!CH}/$SEG_IM_TRACK_PATH
                        done

                        # # generate folders for segmentation-mat files
                        # for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                        #         CH="CHANNEL_$i"
                        #         make_dir $PATH_FOLDER$POS/${!CH}/$SEG_PATH$SEG_MAT_PATH
                        # done

			            # generate folder for tracking output
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                make_dir $PATH_FOLDER$POS/${!CH}/$TRACK_OUT_PATH
                        done
                fi


                # 2) Copy files
                if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                        then
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                VAR=`find $PATH_FOLDER -name *$POS*${!CH}*.$FILE_TYPE`
                                cp $VAR $PATH_FOLDER$POS/${!CH}/
                        done
                fi

                # Restrict frames based on layers of tiff file
                FRAME_NUM=$(identify $VAR | wc -l)
                FRAME_DIFF="$(($END_FRAME-$START_FRAME))"
                if [[ $FRAME_DIFF > $FRAME_NUM ]]
                then
                        END_FRAME="$(($FRAME_NUM-1))"
                        START_FRAME=0
                        echo $END_FRAME
                        echo $START_FRAME
                fi


                # 3) Split frames
                if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                then
                        echo "split frames"
                        for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                CH="CHANNEL_$i"
                                INP=$(find $PATH_FOLDER$POS/${!CH}/ -name *.$FILE_TYPE)
                                python stack2frames.py --path $INP --pos $POS --channel /${!CH}/ --start_frame $START_FRAME --end_frame $END_FRAME --deconv $DECONVOLUTION
                        done
                fi


                # 4) Cut chambers
                if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                then
                        echo "cut chambers"
                        if [ -z "$CHANNEL_2" ] || [ -z "$CHANNEL_3" ]
                                then
                                python frames2cuts.py --path_ch0 $PATH_FOLDER$POS/$CHANNEL_1/$RAW_IM
                                echo $PATH_FOLDER$POS$CHANNEL_1$RAW_IM
                        else
                                python frames2cuts.py --path_ch0 $PATH_FOLDER$POS/$CHANNEL_1/$RAW_IM --path_ch1 $PATH_FOLDER$POS/$CHANNEL_2/$RAW_IM --path_ch2 $PATH_FOLDER$POS/$CHANNEL_3/$RAW_IM
                        fi
                fi


                # 5) Segmentation
                if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                then
                        echo "segment images"
                        if [ "$PHASE_SEGMENTATION" == True ]
                                then 
                                for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                                        CH="CHANNEL_$i"
                                        python main_prediction.py --path_model_weights '../model_weights/model_weights_family_mother_machine/' --path_pos $PATH_FOLDER$POS --path_channel ${!CH} --postprocessing 1 --batch_mode 0
                                        python analyse_segmentation.py --path_seg $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH/ --path_result $PATH_FOLDER$POS/${!CH}/
                                done
                        elif [ "$PHASE_SEGMENTATION" == False ]
                                then
                                for i in $(seq 2 $NUM_CHANNEL_TYPES); do
                                        CH="CHANNEL_$i"
                                        python main_prediction.py --path_model_weights '../model_weights/model_weights_family_mother_machine/' --path_pos $PATH_FOLDER$POS --path_channel ${!CH} --postprocessing 1 --batch_mode 0
                                        python analyse_segmentation.py --path_seg $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH/ --path_result $PATH_FOLDER$POS/${!CH}/
                                done
                        fi
                fi

                # # 6) Conversion
                # if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
                # then
                #         echo "run file-conversion"
                #         for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                #                 CH="CHANNEL_$i"
                #                 python seg2mat.py --path_cut $PATH_FOLDER$POS/${!CH}/$SEG_PATH$CUT_PATH --path_seg $PATH_FOLDER$POS/${!CH}/$SEG_IM_PATH --path_channel $PATH_FOLDER$POS/${!CH}/
                #         done
                # fi


                # 6) Tracking
	        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "TRACKING" ]]
                then
			    echo "run cell tracking"
                if [ "$PHASE_SEGMENTATION" == True ]
                    then 
                	for i in $(seq 1 $NUM_CHANNEL_TYPES); do
                        CH="CHANNEL_$i"
                        python track_cells_crop.py --path $PATH_FOLDER$POS/${!CH}/ --start_frame $START_FRAME --end_frame $END_FRAME
				        python generate_lineages.py --path $PATH_FOLDER$POS/${!CH}/$TRACK_OUT_PATH
                    done
                elif [ "$PHASE_SEGMENTATION" == False ]
                    then
                    for i in $(seq 2 $NUM_CHANNEL_TYPES); do
                        CH="CHANNEL_$i"
                        python track_cells_crop.py --path $PATH_FOLDER$POS/${!CH}/ --start_frame $START_FRAME --end_frame $END_FRAME
				        python generate_lineages.py --path $PATH_FOLDER$POS/${!CH}/$TRACK_OUT_PATH
                    done

                fi


		    fi


    done
fi


if [[ $DATA_TYPE == "WELL" ]]
    then

        PATH_FILE_WO_EXT="${PATH_FILE%.*}"
        FILE_NAME=${PATH_FILE##*/}
        echo $PATH_FILE_WO_EXT
        echo $FILE_NAME

        RAW_IM="raw_im/"
        SEG_PATH="xy1/"
        CUT_PATH="phase/"
        SEG_IM_PATH="seg_im/"
        SEG_MAT_PATH="seg/"
        SEG_IM_TRACK_PATH="input_ilastik_tracking/"

        # 1) Generate folder structure
        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
        then
                echo "generate folder structure"

                # delete results folder in case it already exists
                delete_folder $PATH_FILE_WO_EXT

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

                # generate folder seg_im_track for stacks of segmentation images for tracking
                make_dir $PATH_FILE_WO_EXT/$SEG_IM_TRACK_PATH

                # generate folders for segmentation-mat files
                make_dir $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH
        fi
        
        # 2) Split frames
        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
        then
                echo "split frames"
                python stack2frames.py --path $PATH_FILE_WO_EXT/$FILE_NAME --pos "" --channel "" --start_frame $START_FRAME --end_frame $END_FRAME --deconv $DECONVOLUTION
                cp $PATH_FILE_WO_EXT/$RAW_IM*.$FILE_TYPE $PATH_FILE_WO_EXT/$SEG_PATH$CUT_PATH
        fi
        
        # 3) Segmentation
        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
        then
                echo "segment images"
                python main_prediction.py --path_model_weights '../model_weights/model_weights_well/' --path_pos $PATH_FILE_WO_EXT --path_channel "" --postprocessing 1
        fi

        # 4) Conversion
        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "SEGMENTATION" ]]
        then
                echo "run file-conversion"
                python seg2mat.py --path_cut $PATH_FILE_WO_EXT/$SEG_PATH$CUT_PATH --path_seg $PATH_FILE_WO_EXT/$SEG_IM_PATH --path_channel $PATH_FILE_WO_EXT/
        fi

        # 5) Tracking
        if [[ $RUN_OPTION == "BOTH" ]] || [[ $RUN_OPTION == "TRACKING" ]]
        then
                echo "run tracking"
                # delete all files related to SuperSegger to ensure that SuperSegger runs
                rm $PATH_FILE_WO_EXT/CONST.mat
                rm $PATH_FILE_WO_EXT/$SEG_PATH/clist.mat
                rm $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH/*_err.mat
                rm -r $PATH_FILE_WO_EXT/$SEG_PATH/cell
                rm $PATH_FILE_WO_EXT/$SEG_PATH/$RAW_IM/cropbox.mat

                $MATLAB_ROOT/bin/matlab -nodisplay -r "tracking_supersegger('$PATH_FILE_WO_EXT', '$CONSTANTS' , $NEIGHBOR_FLAG, $TIME_STEP, $MIN_CELL_AGE, '$DATA_TYPE')"

                MAT_FILE=$PATH_FILE_WO_EXT/$SEG_PATH/clist.mat
                # as long as 'clist.mat' is missing (hint for failed SuperSegger) the tracking can be repeated with a reduced number of frames
                while ! test -f "$MAT_FILE"; do
                        rm $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH/*_err.mat
                        rm $PATH_FILE_WO_EXT/CONST.mat
                        rm $PATH_FILE_WO_EXT/$SEG_PATH/$RAW_IM/cropbox.mat

                        python restrict_frames.py
                        source settings.sh
                        LIST_FILES=($(ls $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH))
                        NUM_FILES=${#LIST_FILES[@]}
                        NUM_REMOVE=$NUM_FILES-$END_FRAME #number of files to remove

                        for FILE in ${LIST_FILES[@]:$END_FRAME:$NUM_REMOVE}; do
                                rm $PATH_FILE_WO_EXT/$SEG_PATH$SEG_MAT_PATH/$FILE
                        done
                        $MATLAB_ROOT/bin/matlab -nodisplay -r "tracking_supersegger('$PATH_FILE_WO_EXT', '$CONSTANTS' , $NEIGHBOR_FLAG, $TIME_STEP, $MIN_CELL_AGE, '$DATA_TYPE')"
                done
        fi
fi