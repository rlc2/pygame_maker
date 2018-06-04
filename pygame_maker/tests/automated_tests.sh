#!/bin/sh

TEST_FAILURES=0
FAILED_LIST=
SCRIPT_PATH=`realpath $0`
SCRIPT_DIR=`dirname $SCRIPT_PATH`

if ! $SCRIPT_DIR/test_action.py -v ; then
    FAILED_LIST="$FAILED_LIST test_action.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_action_sequence.py -v ; then
    FAILED_LIST="$FAILED_LIST test_action_sequence.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_color.py -v ; then
    FAILED_LIST="$FAILED_LIST test_color.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_css_to_style.py -v ; then
    FAILED_LIST="$FAILED_LIST test_css_to_style.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_event.py -v ; then
    FAILED_LIST="$FAILED_LIST test_event.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_event_engine.py -v ; then
    FAILED_LIST="$FAILED_LIST test_event_engine.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_infix_to_postfix.py -v ; then
    FAILED_LIST="$FAILED_LIST test_infix_to_postfix.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_code_block.py -v ; then
    FAILED_LIST="$FAILED_LIST test_code_block.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_language_engine.py -v ; then
    FAILED_LIST="$FAILED_LIST test_language_engine.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_styles.py -v ; then
    FAILED_LIST="$FAILED_LIST test_styles.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_object_sprite.py -v ; then
    FAILED_LIST="$FAILED_LIST test_object_sprite.py"
    TEST_FAILURES=1
fi
if ! $SCRIPT_DIR/test_sound.py -v ; then
    FAILED_LIST="$FAILED_LIST test_sound.py"
    TEST_FAILURES=1
fi

if [ "$TEST_FAILURES" != "0" ] ; then
    echo The following tests had failures:
    for FAILED in $FAILED_LIST ; do
        echo $FAILED
    done
else
    echo
    echo All automated tests passed.
fi

exit $TEST_FAILURES

