// 슬라이드 p1-net-il — IL 의 add 는 형식을 모른다, C# 1.0
using System;
using System.Collections;
using System.Reflection;
using System.Reflection.Emit;

class Il
{
    static int AddI(int a, int b) { return a + b; }
    static long AddL(long a, long b) { return a + b; }
    static double AddD(double a, double b) { return a + b; }

    static Hashtable ops = new Hashtable();   // byte -> OpCode

    static void Main()
    {
        foreach (FieldInfo f in typeof(OpCodes).GetFields())
        {
            OpCode op = (OpCode)f.GetValue(null);
            if (op.Size == 1) ops[(int)(op.Value & 0xFF)] = op;
        }
        Dump("AddI"); Dump("AddL"); Dump("AddD");
    }

    static void Dump(string name)
    {
        MethodInfo m = typeof(Il).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        byte[] il = m.GetMethodBody().GetILAsByteArray();
        string s = name + ":";
        for (int i = 0; i < il.Length; i++)
        {
            OpCode op = (OpCode)ops[(int)il[i]];
            s += " " + op.Name;
            if (op.OperandType == OperandType.ShortInlineBrTarget) i++;
        }
        Console.WriteLine(s);
    }
}
