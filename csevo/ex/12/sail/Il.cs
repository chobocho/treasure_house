// 슬라이드 p12-v11-sa-il — IL 을 읽는 작은 해독기, C# 11.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;

static class Il
{
    static readonly Dictionary<short, OpCode> Ops = new();

    static Il()
    {
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
            if (f.GetValue(null) is OpCode op) Ops[op.Value] = op;
    }

    static int Size(OperandType t, byte[] b, int i) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget or OperandType.ShortInlineI
            or OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 or OperandType.InlineR => 8,
        OperandType.InlineSwitch => 4 + 4 * BitConverter.ToInt32(b, i),
        _ => 4,
    };

    // Prints only the opcodes whose operand is a type or a method
    public static void Dump(MethodInfo m)
    {
        byte[] b = m.GetMethodBody().GetILAsByteArray();
        Type[] ta = m.DeclaringType.GetGenericArguments();
        Type[] ma = m.GetGenericArguments();
        for (int i = 0; i < b.Length; )
        {
            short v = b[i] == 0xFE ? (short)(0xFE00 | b[i + 1]) : b[i];
            OpCode op = Ops[v];
            i += op.Size;
            int tok = op.OperandType == OperandType.InlineNone
                ? 0 : BitConverter.ToInt32(b, i);
            string arg = op.OperandType switch
            {
                OperandType.InlineMethod => Name(m.Module
                    .ResolveMethod(tok, ta, ma)),
                OperandType.InlineType =>
                    m.Module.ResolveType(tok, ta, ma).Name,
                _ => null,
            };
            i += Size(op.OperandType, b, i);
            if (arg != null)
                Console.WriteLine("  " + op.Name + " " + arg);
        }
    }

    static string Name(MethodBase mb) =>
        mb.DeclaringType.Name + "::" + mb.Name;
}
