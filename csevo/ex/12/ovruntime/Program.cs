// 슬라이드 p12-v11-runtime — C# 11 기능이 기대는 형식, C# 11.0
using System;

class App
{
    const string N = "System.Numerics.";
    const string CS = "System.Runtime.CompilerServices.";
    const string CA = "System.Diagnostics.CodeAnalysis.";

    static readonly string[] Names =
    {
        N + "INumber`1", N + "IAdditionOperators`3",       // 4장
        CS + "RequiredMemberAttribute",                    // 7장
        CA + "SetsRequiredMembersAttribute",
        CS + "CompilerFeatureRequiredAttribute",
        CA + "UnscopedRefAttribute",                       // 8장
        CS + "ScopedRefAttribute", CS + "RefSafetyRulesAttribute",
        "System.MemoryExtensions",                         // 2장
        "System.Int128",                                   // 4장
    };

    static void Main()
    {
        foreach (string n in Names)
        {
            Type t = Type.GetType(n);
            string where = t is null ? "-" : t.Assembly.GetName().Name;
            int dot = n.LastIndexOf('.');
            Console.WriteLine($"{n[(dot + 1)..],-36} {where}");
        }
    }
}
