// 슬라이드 p13-v12-intercept — 생성기가 썼을 법한 파일, C# 12.0
namespace System.Runtime.CompilerServices
{
    // not in .NET 10: the generator declares it itself
    [AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
    sealed class InterceptsLocationAttribute : Attribute
    {
        public InterceptsLocationAttribute(string filePath,
                                           int line, int character) { }
    }
}

namespace Gen
{
    using System.Runtime.CompilerServices;

    static class Hooks
    {
#if BADCOL
        [InterceptsLocation("Program.cs", 8, 27)]   // 'Calc'
#elif BADPATH
        [InterceptsLocation("Prog.cs", 8, 32)]
#else
        [InterceptsLocation("Program.cs", 8, 32)]
#endif
        public static int Twice(int x) => -x;
    }
}
