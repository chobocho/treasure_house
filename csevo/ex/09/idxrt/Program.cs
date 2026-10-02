// 슬라이드 p9-v8-idx-runtime — ^·.. 가 기대는 런타임 형식, C# 8.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        foreach (Type t in new[] { typeof(Index), typeof(Range) })
        {
            Console.WriteLine("{0} [{1}] value type: {2}", t.FullName,
                t.Assembly.GetName().Name, t.IsValueType);
            var names = t.GetMembers(BindingFlags.Public |
                    BindingFlags.Instance | BindingFlags.Static |
                    BindingFlags.DeclaredOnly)
                .Where(m => m.MemberType != MemberTypes.Method ||
                            !((MethodInfo)m).IsSpecialName)
                .Select(m => m.Name).Distinct().OrderBy(n => n);
            Console.WriteLine("  " + string.Join(" ", names));
        }
        MethodInfo sub =
            typeof(RuntimeHelpers).GetMethod("GetSubArray");
        Console.WriteLine(sub);
    }
}
