// 슬라이드 p7-v6-roslyn-comp — 프로그램 안의 컴파일러, C# 6.0
using System;
using System.IO;
using System.Reflection;

class App
{
    const string Src = @"
class C
{
    static void Main() { }
    public static string Hello(string who)
    {
        return $""hello, {who?.ToUpper() ?? ""nobody""}"";
    }
}";

    static void Main()
    {
        foreach (string v in new[] { "CSharp5", "CSharp6" })
        {
            dynamic comp = Csc.Compile(Src, v);
            Console.WriteLine(v + ":");
            foreach (dynamic d in comp.GetDiagnostics())
                Console.WriteLine("  " + d.ToString());
            var pe = new MemoryStream();
            if (!comp.Emit(pe).Success) continue;
            MethodInfo hello = Assembly.Load(pe.ToArray())
                .GetType("C").GetMethod("Hello");
            Console.WriteLine("  " + hello.Invoke(null, new[] {"ada"}));
            Console.WriteLine("  " + hello.Invoke(null, new object[1]));
        }
    }
}
