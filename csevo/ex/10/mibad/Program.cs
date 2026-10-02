// 슬라이드 p10-v9-mi-rules — 모듈 초기화자가 될 수 없는 메서드, C# 9.0
using System.Runtime.CompilerServices;

#if !LOCAL
class Bad
{
    [ModuleInitializer] internal void Instance() { }
    [ModuleInitializer] internal static void Args(int x) { }
    [ModuleInitializer] internal static int Value() => 0;
    [ModuleInitializer] internal static void Generic<T>() { }
    [ModuleInitializer] private static void Hidden() { }
}

class Box<T>
{
    [ModuleInitializer] internal static void InGeneric() { }
}
#endif

class App
{
    static void Main()
    {
#if LOCAL
        [ModuleInitializer] static void Local() { }
        Local();
#endif
    }
}
