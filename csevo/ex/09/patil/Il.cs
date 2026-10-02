// 슬라이드 p9-v8-pat-il — IL 에서 호출 대상만 뽑는 도구, C# 8.0
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

    static int Size(OperandType t, byte[] il, int i) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget => 1,
        OperandType.ShortInlineI => 1,
        OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 => 8,
        OperandType.InlineR => 8,
        OperandType.InlineSwitch => 4 + 4 * BitConverter.ToInt32(il, i),
        _ => 4,
    };
    // call / callvirt / newobj targets in IL order, O(IL length)
    public static List<string> Calls(MethodInfo m)
    {
        var r = new List<string>();
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        for (int i = 0; i < il.Length;)
        {
            int v = il[i] == 0xFE ? 0xFE00 | il[i + 1] : il[i];
            i += il[i] == 0xFE ? 2 : 1;
            OpCode op = ops[v];
            if (op.OperandType == OperandType.InlineMethod)
            {
                MethodBase c = m.Module.ResolveMethod(
                    BitConverter.ToInt32(il, i));
                r.Add(op.Name + " " + c.DeclaringType.Name + "."
                      + c.Name);
            }
            i += Size(op.OperandType, il, i);
        }
        return r;
    }
}
