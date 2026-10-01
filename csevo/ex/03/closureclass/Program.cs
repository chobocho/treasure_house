// 슬라이드 p3-v2-closure-class — 컴파일러가 만드는 클래스, C# 2.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

delegate int Counter();

class App
{
    static Counter Make(int start)
    {
        int n = start;
        return delegate { n++; return n; };
    }

    static void Main()
    {
        Counter c = Make(10);
        object t = c.Target;
        Type tt = t.GetType();
        Type cg = typeof(CompilerGeneratedAttribute);
        Console.WriteLine("nested in " + tt.DeclaringType.Name);
        Console.WriteLine("generated " + tt.IsDefined(cg, false));
        FieldInfo[] fs = tt.GetFields();
        foreach (FieldInfo f in fs)
            Console.WriteLine("field " + f.FieldType.Name
                + " " + f.Name);
        c();
        c();
        Console.WriteLine("n is now " + fs[0].GetValue(t));
        Console.WriteLine("method is static: " + c.Method.IsStatic);
    }
}
