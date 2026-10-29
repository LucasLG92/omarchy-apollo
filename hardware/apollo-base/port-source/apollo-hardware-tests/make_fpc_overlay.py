from pathlib import Path
import struct,sys
b=Path(sys.argv[1]).read_bytes()
magic,total,off,strings=struct.unpack_from('>IIII',b)
assert magic==0xd00dfeed
stack=[]; regulator=None; tlmm=None; native_fpc=False
while off < total:
    token=struct.unpack_from('>I',b,off)[0]; off+=4
    if token==1:
        end=b.index(0,off); stack.append(b[off:end].decode()); off=(end+4)&~3
        if '/'.join(stack)=='/apollo-fpc-test': native_fpc=True
    elif token==2: stack.pop()
    elif token==3:
        length,nameoff=struct.unpack_from('>II',b,off); off+=8
        name=b[strings+nameoff:b.index(0,strings+nameoff)].decode()
        value=b[off:off+length]; off=(off+length+3)&~3
        path='/'.join(stack)
        if name=='regulator-name' and value==b'vreg_l8c_1p8\0': regulator=path
        if name=='phandle' and path=='/soc@0/pinctrl@f100000': tlmm=struct.unpack('>I',value)[0]
    elif token==4: pass
    elif token==9: break
    else: raise ValueError(token)
assert regulator and tlmm
if native_fpc:
    Path(sys.argv[2]).write_text('''/dts-v1/;
/plugin/;
/ { fragment@0 { target-path = "/apollo-fpc-test"; __overlay__ { status = "okay"; }; }; };
''')
    print('Generated RAM enable overlay for the compiled FPC board node')
    raise SystemExit(0)
s='''/dts-v1/;
/plugin/;
/ {
    fragment@0 {
        target-path = "@VDD@";
        fpc_supply: __overlay__ {};
    };
    fragment@1 {
        target-path = "/soc@0/pinctrl@f100000";
        __overlay__ {
            apollo_fpc_pins: apollo-fpc-pins {
                reset { pins = "gpio24"; function = "gpio"; drive-strength = <2>; bias-disable; };
                irq { pins = "gpio23"; function = "gpio"; drive-strength = <2>; bias-pull-down; input-enable; };
            };
        };
    };
    fragment@2 {
        target-path = "/";
        __overlay__ {
            apollo-fpc-test {
                compatible = "xiaomi,apollo-fpc-test";
                vdd-supply = <&fpc_supply>;
                reset-gpios = <@TLMM@ 24 1>;
                irq-gpios = <@TLMM@ 23 0>;
                pinctrl-names = "default";
                pinctrl-0 = <&apollo_fpc_pins>;
            };
        };
    };
};
'''.replace('@VDD@',regulator).replace('@TLMM@',hex(tlmm))
Path(sys.argv[2]).write_text(s)
print('Generated board-specific RAM overlay:',regulator,'TLMM',hex(tlmm))
