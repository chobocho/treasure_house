// 슬라이드 p12-v11-ad-lower — 생성자의 IL 을 한 줄로 찍는 해독기, C# 11
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;

static class Il
{
    static readonly Dictionary<short, OpCode> Table = new();

    static Il()
    {
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
            if (f.GetValue(null) is OpCode op) Table[op.Value] = op;
    }

    static int Size(OperandType t) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget or OperandType.ShortInlineI
            or OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 or OperandType.InlineR => 8,
        _ => 4,             // no switch in these constructors
    };

    // Every opcode except nop; fields, types and methods by name
    public static List<string> Ops(MethodBase m)
    {
        byte[] b = m.GetMethodBody().GetILAsByteArray();
        var parts = new List<string>();
        for (int i = 0; i < b.Length; )
        {
            short v = b[i] == 0xFE ? (short)(0xFE00 | b[i + 1]) : b[i];
            OpCode op = Table[v];
            i += op.Size;
            int tok = op.OperandType == OperandType.InlineNone
                ? 0 : BitConverter.ToInt32(b, i);
            Module mod = m.Module;
            string arg = op.OperandType switch
            {
                OperandType.InlineField => mod.ResolveField(tok).Name,
                OperandType.InlineType => mod.ResolveType(tok).Name,
                OperandType.InlineMethod => mod.ResolveMethod(tok).Name,
                _ => null,
            };
            i += Size(op.OperandType);
            if (op != OpCodes.Nop)
                parts.Add(arg == null ? op.Name : op.Name + " " + arg);
        }
        return parts;
    }
}
