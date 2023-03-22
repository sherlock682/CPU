# coding=utf-8

import os
import pin
import assembly as ASM

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname,'micro.bin')

mico = [pin.HLT for _ in range(0x10000)]

CJMPS = {ASM.JO,ASM.JNO,ASM.JZ,ASM.JNZ,ASM.JP,ASM.JNP}

def compile_addr2(addr,ir,psw,index):
    global mico

    op = ir & 0xf0
    amd = (ir >>2) & 3
    ams = ir & 3

    INST = ASM.INSTRUCTIONS[2]
    if op not in INST:
        mico[addr] = pin.CYC
        return
    am = (amd,ams)
    if am not in INST[op]:
        mico[addr] = pin.CYC
        return

    EXEC = INST[op][am]
    if index < len(EXEC):
        mico[addr] = EXEC[index]
    else:
        mico[addr] = pin.CYC

def get_condition_jump(exec,op,psw):
    overflow = psw & 1
    zero = psw & 2
    parity = psw & 4

    if op == ASM.JO and overflow:
        return exec
    if op == ASM.JNO and not overflow:
        return exec
    if op == ASM.JZ and zero:
        return exec
    if op == ASM.JNZ and not zero:
        return exec
    if op == ASM.JP and parity:
        return exec
    if op == ASM.JNP and not parity:
        return exec
    return [pin.CYC]

def get_interrupt(exec, op, psw):
    interrupt = psw & 8
    if interrupt:
        return exec
    return [pin.CYC]

def compile_addr1(addr,ir,psw,index):
    global mico
    global CJMPS

    op = ir & 0xfc
    amd = ir & 3

    INST = ASM.INSTRUCTIONS[1]
    if op not in INST:
        mico[addr] = pin.CYC
        return

    if amd not in INST[op]:
        mico[addr] = pin.CYC
        return

    EXEC = INST[op][amd]
    if op in CJMPS:
        EXEC = get_condition_jump(EXEC, op, psw)
    if op ==ASM.INT:
        EXEC = get_interrupt(EXEC, op, psw)
        
    if index < len(EXEC):
        mico[addr] = EXEC[index]
    else:
        mico[addr] = pin.CYC


def compile_addr0(addr,ir,psw,index):
    global mico

    op = ir 
    
    INST = ASM.INSTRUCTIONS[0]
    if op not in INST:
        mico[addr] = pin.CYC
        return

    EXEC = INST[op]
    if index < len(EXEC):
        mico[addr] = EXEC[index]
    else:
        mico[addr] = pin.CYC


for addr in range(0x10000):
    ir = addr >> 8
    psw = (addr >> 4) & 0xf
    cyc = addr & 0xf

    if cyc < len(ASM.FETCH):
        mico[addr] = ASM.FETCH[cyc]
        continue

    addr2 = ir & (1 << 7)
    addr1 = ir & (1 << 6)

    index = cyc - len(ASM.FETCH)

    if addr2:
        compile_addr2(addr,ir,psw,index)
    elif addr1:
        compile_addr1(addr,ir,psw,index)
    else:
        compile_addr0(addr,ir,psw,index)


with open(filename,'wb') as file:
    for var in mico:
        value = var.to_bytes(4,byteorder='little')
        file.write(value)

print('Compiling mico instructing finish!!!')