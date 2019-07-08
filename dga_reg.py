#!/usr/bin/env python3
from dataclasses import dataclass
import dataclasses
import re

@dataclass
class RegisterRegion:
    regNum: int
    subRegNum:int
    vertical: int
    euType: str
    width: int = 1
    horizontal: int = 0

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            newValue = field.type(value) if value is not None else field.default 
            setattr(self, field.name, newValue)

    @property
    def bytes(self) -> int:
        d_type = {#integer
                  'ub':1, 'b':1,
                  'uw':2, 'w':2,
                  'f':4, 'ud':4,
                  'd':4, 'uq':4,
                  'q':4, 'uv':2,
                  'v':2,
                  #floating-point
                  'hf':2, 'f':4,
                  'df':8,'vf':4}
        return d_type[self.euType]


def genRegisterPosition(simdWidth, register, 
                        regex = re.compile(r"r(?P<regNum>\d+)\.(?P<subRegNum>\d+)<(?P<vertical>\d+)(?:;(?P<width>\d+),(?P<horizontal>\d+))?>:(?P<euType>\w+)")):
        fn_dict = regex.match(register).groupdict()
        register = RegisterRegion(**fn_dict)

        x0 = register.subRegNum * register.bytes
        y = register.regNum

        for _ in range(simdWidth // register.width):

            # Populate the row.
            for i in range(register.width):    
                x =  x0 + i * register.horizontal * register.bytes
                yield y, tuple(x+b for b in range(register.bytes))

            # Apply vertical offset
            # Compute the new starting point of the row, and the collum
            y_, x0 = divmod(x0 + register.vertical * register.bytes,32)
            y += y_
    

import unittest

class TestRegisterPosition(unittest.TestCase):

    # https://software.intel.com/en-us/articles/introduction-to-gen-assembly
    def test_Fig16(self):
        l = list(genRegisterPosition(16, 'r4.1<16;8,2>:w'))
        gold = [(4, (2, 3)), (4, (6, 7)), (4, (10, 11)), (4, (14, 15)), (4, (18, 19)), (4, (22, 23)), (4, (26, 27)), (4, (30, 31)),
                (5, (2, 3)), (5, (6, 7)), (5, (10, 11)), (5, (14, 15)), (5, (18, 19)), (5, (22, 23)), (5, (26, 27)), (5, (30, 31))]
        self.assertEqual(l, gold)

    def test_Fig17(self):
        l = list(genRegisterPosition(16, 'r5.0<1;8,2>:w'))
        gold = [(5, (0, 1)), (5, (4, 5)), (5, (8, 9)), (5, (12, 13)), (5, (16, 17)), (5, (20, 21)), (5, (24, 25)), (5, (28, 29)), 
                (5, (2, 3)), (5, (6, 7)), (5, (10, 11)), (5, (14, 15)), (5, (18, 19)), (5, (22, 23)), (5, (26, 27)), (5, (30, 31))]
        self.assertEqual(l, gold)

    def test_Fig18_dst(self):
        l = list(genRegisterPosition(16, 'r6.0<1>:w'))
        gold = [(6, (0, 1)), (6, (2, 3)), (6, (4, 5)), (6, (6, 7)), (6, (8, 9)), (6, (10, 11)), (6, (12, 13)), (6, (14, 15)),
                (6, (16, 17)), (6, (18, 19)), (6, (20, 21)), (6, (22, 23)), (6, (24, 25)), (6, (26, 27)), (6, (28, 29)), (6, (30, 31))]
        self.assertEqual(l, gold)

    def test_Fig18_src0(self):
        l = list(genRegisterPosition(16, 'r1.7<16;8,1>:b'))
        gold = [(1, (7,)), (1, (8,)), (1, (9,)), (1, (10,)), (1, (11,)), (1, (12,)), (1, (13,)), (1, (14,)), 
                (1, (23,)), (1, (24,)), (1, (25,)), (1, (26,)), (1, (27,)), (1, (28,)), (1, (29,)), (1, (30,))]
        self.assertEqual(l, gold)

    def test_Fig18_src1(self):
        l = list(genRegisterPosition(16, 'r2.1<16;8,1>:b'))
        gold = [(2, (1,)), (2, (2,)), (2, (3,)), (2, (4,)), (2, (5,)), (2, (6,)), (2, (7,)), (2, (8,)), 
                (2, (17,)), (2, (18,)), (2, (19,)), (2, (20,)), (2, (21,)), (2, (22,)), (2, (23,)), (2, (24,))]
        self.assertEqual(l, gold)

    def test_Fig19_dst(self):
        l = list(genRegisterPosition(16, 'r6.0<1>:w'))
        gold = [(6, (0, 1)), (6, (2, 3)), (6, (4, 5)), (6, (6, 7)), (6, (8, 9)), (6, (10, 11)), (6, (12, 13)), (6, (14, 15)), (6, (16, 17)), (6, (18, 19)), (6, (20, 21)), (6, (22, 23)), (6, (24, 25)), (6, (26, 27)), (6, (28, 29)), (6, (30, 31))]
        self.assertEqual(l, gold)

    def test_Fig19_src0(self):
        l = list(genRegisterPosition(16, 'r1.14<16;8,0>:b'))
        gold = [(1, (14,)), (1, (14,)), (1, (14,)), (1, (14,)), (1, (14,)), (1, (14,)), (1, (14,)), (1, (14,)), (1, (30,)), (1, (30,)), (1, (30,)), (1, (30,)), (1, (30,)), (1, (30,)), (1, (30,)), (1, (30,))]
        self.assertEqual(l, gold)

    def test_Fig19_src1(self):
        l = list(genRegisterPosition(16, 'r2.17<16;8,1>:b'))
        gold = [(2, (17,)), (2, (18,)), (2, (19,)), (2, (20,)), (2, (21,)), (2, (22,)), (2, (23,)), (2, (24,)), (3, (1,)), (3, (2,)), (3, (3,)), (3, (4,)), (3, (5,)), (3, (6,)), (3, (7,)), (3, (8,))]
        self.assertEqual(l, gold)

    #A21 COE Day2 Apr 23 2019, An introduction to gen assembly language
    def test_slide101_yellow(self):
        l = list(genRegisterPosition(8, 'r2.1<1>:w'))
        gold = [(2, (2, 3)), (2, (4, 5)), (2, (6, 7)), (2, (8, 9)), (2, (10, 11)), (2, (12, 13)), (2, (14, 15)), (2, (16, 17))]
        self.assertEqual(l, gold)


    def test_slide101_blue(self):
        l = list(genRegisterPosition(8, 'r3.5<1>:f'))
        # wrong in the slide
        gold = [(3, (20, 21, 22, 23)), (3, (24, 25, 26, 27)), (3, (28, 29, 30, 31)), (4, (0, 1, 2, 3)), (4, (4, 5, 6, 7)), (4, (8, 9, 10, 11)), (4, (12, 13, 14, 15)), (4, (16, 17, 18, 19))]
        self.assertEqual(l, gold)

    def test_slide101_red(self):
        l = list(genRegisterPosition(8, 'r6.0<2>:w'))
        gold =[(6, (0, 1)), (6, (4, 5)), (6, (8, 9)), (6, (12, 13)), (6, (16, 17)), (6, (20, 21)), (6, (24, 25)), (6, (28, 29))]
        self.assertEqual(l, gold)


    def test_slide101_green(self):
        # Illegal register
        l = list(genRegisterPosition(8, 'r7.0<4>:f'))
        gold =[(7, (0, 1, 2, 3)), (7, (16, 17, 18, 19)), 
               (8, (0, 1, 2, 3)), (8, (16, 17, 18, 19)),
               (9, (0, 1, 2, 3)), (9, (16, 17, 18, 19)),
               (10, (0, 1, 2, 3)), (10, (16, 17, 18, 19))]
        self.assertEqual(l, gold)

    def test_slide112_packed_acceses_1(self):
        l = list(genRegisterPosition(16, 'r0.0<8;8,1>:f'))
        gold =[(0, (0, 1, 2, 3)), (0, (4, 5, 6, 7)), (0, (8, 9, 10, 11)), (0, (12, 13, 14, 15)), (0, (16, 17, 18, 19)), (0, (20, 21, 22, 23)), (0, (24, 25, 26, 27)), (0, (28, 29, 30, 31)),
               (1, (0, 1, 2, 3)), (1, (4, 5, 6, 7)), (1, (8, 9, 10, 11)), (1, (12, 13, 14, 15)), (1, (16, 17, 18, 19)), (1, (20, 21, 22, 23)), (1, (24, 25, 26, 27)), (1, (28, 29, 30, 31))]
        self.assertEqual(l, gold)


    def test_slide112_packed_acceses_2(self):
        l = list(genRegisterPosition(16, 'r2.8<16;16,1>:hf'))
        #Invalid. To check the image it should have been 'r2.8<16;8,1>:hf'
        pass

    def test_slide112_packed_acceses_3(self):
        l = list(genRegisterPosition(8, 'r4.0<8;8,1>:df'))
        #Invalid. To check the image it should have been 'r4.0<8;4,1>:df'
        pass

    def test_slide112_broadcast(self):
        l = list(genRegisterPosition(1, 'r6.3<0;1,0>:f'))
        gold = [(6, (12, 13, 14, 15))]
        self.assertEqual(l, gold)

    def test_slide112_strided_block(self):
        l = list(genRegisterPosition(8, 'r7.1<4;1,0>:b'))
        gold = [(7, (1,)), (7, (5,)), (7, (9,)), (7, (13,)), (7, (17,)), (7, (21,)), (7, (25,)), (7, (29,))]
        self.assertEqual(l, gold)

    def test_slide112_permutations_and_weighted_overlap_windows_1(self):
        l = list(genRegisterPosition(8, 'r9.0<1;2,4>:d'))
        # Wrong in the slide it should have been r9.0<1;4,2>:w
        pass

        #gold = [(9, (0, 1, 2, 3)), (9, (16, 17, 18, 19)), (9, (4, 5, 6, 7)), (9, (20, 21, 22, 23)), 
        #        (9, (8, 9, 10, 11)), (9, (24, 25, 26, 27)), (9, (12, 13, 14, 15)), (9, (28, 29, 30, 31))]
        #self.assertEqual(l, gold)

if __name__ == '__main__':
    unittest.main()



