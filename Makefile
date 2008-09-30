PYTHONPATH:=$(shell pwd)/lib:${PYTHONPATH}

all:

check:
	PYTHONPATH=$(PYTHONPATH) python ./test_all.py $(TESTRULE)

clean:
	find . -name '*.pyc' -print0 | xargs -0 rm -f

TAGS: lib/testresources/*.py lib/testresources/tests/*.py
	ctags -e -R lib/testresources/

tags: lib/testresources/*.py lib/testresources/tests/*.py
	ctags -R lib/testresources/

.PHONY: all check clean
