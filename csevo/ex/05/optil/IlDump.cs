// 슬라이드 p5-v4-opt-il — IL 을 읽는 작은 도구, C# 4.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;

static class IlDump
{
    static Dictionary<short, OpCode> ops =
        new Dictionary<short, OpCode>();

    static IlDump()
    {
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
        {
            OpCode op = (OpCode)f.GetValue(null);
            ops[op.Value] = op;
        }
    }

    public static void Print(MethodInfo m)
    {
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        for (int i = 0; i < il.Length; )
        {
            short v = il[i] != 0xFE ? il[i]
                    : (short)(0xFE00 | il[i + 1]);
            OpCode op = ops[v];
            i += op.Size;
            string arg = "";
            int n = op.OperandType == OperandType.InlineNone ? 0
                  : op.OperandType == OperandType.ShortInlineI ? 1 : 4;
            if (n == 1) arg = ((sbyte)il[i]).ToString();
            if (op.OperandType == OperandType.InlineString)
                arg = "\"" + m.Module.ResolveString(
                          BitConverter.ToInt32(il, i)) + "\"";
            if (op.OperandType == OperandType.InlineMethod)
                arg = m.Module.ResolveMethod(
                          BitConverter.ToInt32(il, i)).Name;
            Console.WriteLine(("  " + op.Name.PadRight(11) + arg)
                              .TrimEnd());
            i += n;
        }
    }
}
