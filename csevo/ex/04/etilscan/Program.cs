// 슬라이드 p4-v3-et-factory — 컴파일러가 쓴 것은 팩토리 호출, C# 3.0
using System;
using System.Linq.Expressions;
using System.Reflection;

class Program
{
    static Expression<Func<int, bool>> Make()
    {
        return x => x > 1;
    }

    static void Main()
    {
        MethodInfo m = typeof(Program).GetMethod("Make",
            BindingFlags.NonPublic | BindingFlags.Static);
        byte[] il = m.GetMethodBody().GetILAsByteArray();

        // naive scan: opcode 0x28 is "call", followed by a token
        for (int i = 0; i + 4 < il.Length; i++)
        {
            if (il[i] != 0x28) continue;
            int token = BitConverter.ToInt32(il, i + 1);
            MethodBase callee = m.Module.ResolveMethod(token);
            Console.WriteLine("call " + callee.DeclaringType.Name
                              + "." + callee.Name);
            i += 4;
        }
        Console.WriteLine(Make());
    }
}
