// 슬라이드 p6-v5-caller-const — 호출하는 쪽 IL 에 박힌 상수, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Log([CallerMemberName] string m = "",
        [CallerLineNumber] int line = 0) { }

    static void Caller()
    {
        Log();
    }

    static void Main()
    {
        MethodInfo mi = typeof(App).GetMethod("Caller",
            BindingFlags.NonPublic | BindingFlags.Static);
        Module mod = mi.Module;
        byte[] il = mi.GetMethodBody().GetILAsByteArray();
        Console.WriteLine(BitConverter.ToString(il));
        // Decode only the opcodes this tiny body uses.
        for (int i = 0; i < il.Length; i++)
        {
            byte op = il[i];
            int t = i + 4 < il.Length
                ? BitConverter.ToInt32(il, i + 1) : 0;
            string s = op == 0x00 ? "nop" : op == 0x2A ? "ret"
                : op == 0x1F ? "ldc.i4.s " + il[i + 1]
                : op == 0x72 ? "ldstr \"" + mod.ResolveString(t) + "\""
                : op == 0x28 ? "call " + mod.ResolveMethod(t).Name
                : "?";
            Console.WriteLine(s);
            i += op == 0x1F ? 1 : op == 0x72 || op == 0x28 ? 4 : 0;
        }
    }
}
