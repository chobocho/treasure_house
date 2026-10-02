// 슬라이드 p7-v6-interp-il — IL 에서 호출 대상 읽기, C# 6.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using T = System.Reflection.Emit.OperandType;

static class Il
{
    static Dictionary<short, OpCode> ops =
        new Dictionary<short, OpCode>();

    static int OperandSize(T t)
    {
        if (t == T.InlineNone) return 0;
        if (t == T.ShortInlineBrTarget || t == T.ShortInlineI
            || t == T.ShortInlineVar) return 1;
        if (t == T.InlineVar) return 2;
        if (t == T.InlineI8 || t == T.InlineR) return 8;
        return 4;               // no switch opcodes in our methods
    }

    // print every call/callvirt/newobj target of a method
    public static void Calls(MethodInfo m)
    {
        if (ops.Count == 0)
            foreach (FieldInfo f in typeof(OpCodes).GetFields())
            {
                OpCode o = (OpCode)f.GetValue(null);
                ops[o.Value] = o;
            }
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        for (int i = 0; i < il.Length; )
        {
            OpCode op = ops[il[i] == 0xFE ? (short)(0xFE00 | il[i + 1])
                                          : il[i]];
            i += op.Size;
            if (op.OperandType == T.InlineMethod)
            {
                MethodBase c = m.Module.ResolveMethod(
                    BitConverter.ToInt32(il, i));
                Console.WriteLine("  {0} {1}.{2}({3})", op.Name,
                    c.DeclaringType.Name, c.Name,
                    c.GetParameters().Length);
            }
            i += OperandSize(op.OperandType);
        }
    }
}
