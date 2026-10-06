// 슬라이드 p13-v12-ce-lower — IL 에서 호출·할당만 뽑는 도구, C# 12
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;

static class Il
{
    static readonly Dictionary<short, OpCode> ops = new();

    static Il()
    {
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
            if (f.GetValue(null) is OpCode op) ops[op.Value] = op;
    }

    static int OperandSize(OperandType t) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget or OperandType.ShortInlineI
            or OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 or OperandType.InlineR => 8,
        _ => 4,               // no switch opcodes in these methods
    };

    // call, newobj, newarr, ldtoken ... of one method, in IL order
    public static void Calls(string name)
    {
        var m = typeof(Program).GetMethod(name,
            BindingFlags.Static | BindingFlags.NonPublic);
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        Console.WriteLine(name + ":");
        for (int i = 0; i < il.Length;)
        {
            OpCode op = ops[il[i] == 0xFE
                ? (short)(0xFE00 | il[i + 1]) : il[i]];
            i += op.Size;
            if (op.OperandType is OperandType.InlineMethod
                or OperandType.InlineType or OperandType.InlineTok)
            {
                var mi = m.Module.ResolveMember(
                    BitConverter.ToInt32(il, i));
                string nm = mi.Name.Length > 24
                    ? mi.Name[..8] + "…" : mi.Name;
                Console.WriteLine("  " + op.Name.PadRight(9)
                    + (mi is Type ? "" : mi.DeclaringType.Name + ".")
                    + nm);
            }
            i += OperandSize(op.OperandType);
        }
    }
}
