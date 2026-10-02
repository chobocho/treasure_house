// 슬라이드 p10-v9-fnptr-il — IL 명령을 차례로 뽑는 도구, C# 9.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;

static class Il
{
    static readonly Dictionary<int, OpCode> ops = Load();

    static Dictionary<int, OpCode> Load()
    {
        var d = new Dictionary<int, OpCode>();
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
        {
            var op = (OpCode)f.GetValue(null);
            d[(ushort)op.Value] = op;
        }
        return d;
    }

    static int Size(OperandType t) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget or OperandType.ShortInlineI
            or OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 or OperandType.InlineR => 8,
        _ => 4,                  // no switch opcode in these methods
    };

    // opcode names in IL order, call targets resolved. O(IL length)
    public static List<string> Ops(MethodInfo m)
    {
        var r = new List<string>();
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        for (int i = 0; i < il.Length;)
        {
            int v = il[i] == 0xFE ? 0xFE00 | il[i + 1] : il[i];
            i += il[i] == 0xFE ? 2 : 1;
            OpCode op = ops[v];
            string s = op.Name;
            if (op.OperandType == OperandType.InlineMethod)
            {
                MethodBase c = m.Module.ResolveMethod(
                    BitConverter.ToInt32(il, i));
                s += " " + c.DeclaringType.Name + "." + c.Name;
            }
            r.Add(s);
            i += Size(op.OperandType);
        }
        return r;
    }
}
