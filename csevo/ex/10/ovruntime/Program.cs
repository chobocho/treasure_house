// 슬라이드 p10-v9-runtime — C# 9 가 기대는 런타임과 라이브러리, C# 9.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t, string usedBy)
    {
        Console.WriteLine("{0,-28} {1,-24} {2}", t.Name,
            t.Assembly.GetName().Name, usedBy);
    }

    static void Main()
    {
        Show(typeof(IsExternalInit), "init");
        Show(typeof(ModuleInitializerAttribute), "[ModuleInitializer]");
        Show(typeof(SkipLocalsInitAttribute), "[SkipLocalsInit]");
        Show(typeof(nint), "nint");
        Console.WriteLine("CovariantReturnsOfClasses: {0}",
            RuntimeFeature.IsSupported(
                RuntimeFeature.CovariantReturnsOfClasses));
        Console.WriteLine("runtime {0}", Environment.Version);
    }
}
