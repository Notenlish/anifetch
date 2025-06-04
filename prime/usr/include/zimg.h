#ifndef ZIMG_H_
#define ZIMG_H_

#include <stddef.h>

/* Support for ELF hidden visibility. DLL targets use export maps instead. */
#if defined(_WIN32) || defined(__CYGWIN__)
  #define ZIMG_VISIBILITY
#elif defined(__GNUC__)
  #define ZIMG_VISIBILITY __attribute__((visibility("default")))
#else
  #define ZIMG_VISIBILITY
#endif

#ifdef __cplusplus
extern "C" {
#endif

/** @file */

/**
 * Greatest version of API described by this header.
 *
 * A number of structure definitions described in this header begin with
 * a member indicating the API version used by the caller. Whenever such
 * a structure is a parameter to a function, the version field should be set
 * to the API version corresponding to its layout to ensure that the library
 * does not access memory beyond the end of the structure.
 */
#define ZIMG_MAKE_API_VERSION(x, y) (((x) << 8) | (y))
#define ZIMG_API_VERSION_MAJOR 2
#define ZIMG_API_VERSION_MINOR 4
#define ZIMG_API_VERSION ZIMG_MAKE_API_VERSION(ZIMG_API_VERSION_MAJOR, ZIMG_API_VERSION_MINOR)

/**
 * Get the version number of the library.
 *
 * This function should not be used to query for API details.
 * Instead, use {@link zimg_get_api_version} to obtain the API version.
 *
 * @see zimg_get_api_version
 *
 * @pre major != 0 && minor != 0 && micro != 0
 * @param[out] major set to the major version
 * @param[out] minor set to the minor verison
 * @param[out] micro set to the micro (patch) version
 */
ZIMG_VISIBILITY
void zimg_get_version_info(unsigned *major, unsigned *minor, unsigned *micro);

/**
 * Get the API version supported by the library.
 * The API version is separate from the library version.
 *
 * @see zimg_get_version_info
 *
 * @param[out] major set to the major version, may be NULL
 * @param[out] minor set to the minor version, may be NULL
 * @return composite API version number
 */
ZIMG_VISIBILITY
unsigned zimg_get_api_version(unsigned *major, unsigned *minor);

/**
 * Library error codes.
 *
 * The error code is a 15-bit quantity with a 5-bit category indicator in the
 * upper bits and a 10-bit error code in the lower bits. The library may also
 * return negative error codes which do not belong to any category, as well as
 * error codes with a category of 0.
 *
 * API functions may return error codes not listed in this header.
 */
typedef enum zimg_error_code_e {
	ZIMG_ERROR_UNKNOWN = -1,
	ZIMG_ERROR_SUCCESS = 0,

	ZIMG_ERROR_OUT_OF_MEMORY        = 1, /**< Not always detected on some platforms. */
	ZIMG_ERROR_USER_CALLBACK_FAILED = 2, /**< User-defined callback failed. */

	/**
	 * An API invariant was violated, or an impossible operation was requested.
	 *
	 * It is the responsibility of the caller to ensure that such conditions do
	 * not occur. Not all illegal operations are detected by the library, and in
	 * general undefined behaviour may occur.
	 */
	ZIMG_ERROR_LOGIC                 = (1 << 10),
	ZIMG_ERROR_GREYSCALE_SUBSAMPLING = ZIMG_ERROR_LOGIC + 1, /**< Attempt to subsample greyscale image */
	ZIMG_ERROR_COLOR_FAMILY_MISMATCH = ZIMG_ERROR_LOGIC + 2, /**< Illegal combination of color family and matrix coefficients. */
	ZIMG_ERROR_IMAGE_NOT_DIVISIBLE   = ZIMG_ERROR_LOGIC + 3, /**< Image dimension does not fit a modulo constraint. */
	ZIMG_ERROR_BIT_DEPTH_OVERFLOW    = ZIMG_ERROR_LOGIC + 4, /**< Bit depth greater than underlying storage format. */

	/**
	 * A function parameter was passed an illegal value.
	 *
	 * While all API errors result from illegal parameters, this category
	 * indicates a locally determinable error, such as an out of range enum.
	 */
	ZIMG_ERROR_ILLEGAL_ARGUMENT   = (2 << 10),
	ZIMG_ERROR_ENUM_OUT_OF_RANGE  = ZIMG_ERROR_ILLEGAL_ARGUMENT + 1, /**< Value not in enumeration. */
	ZIMG_ERROR_INVALID_IMAGE_SIZE = ZIMG_ERROR_ILLEGAL_ARGUMENT + 2, /**< Image size or region is not well-formed. */

	/**
	 * A requested conversion was not supported by the library.
	 *
	 * Some conversions are well-defined but not implemented by the library.
	 * If the conversion is logically impossible, {@link ZIMG_ERROR_LOGIC} may
	 * occur.
	 */
	ZIMG_ERROR_UNSUPPORTED_OPERATION      = (3 << 10),
	ZIMG_ERROR_UNSUPPORTED_SUBSAMPLING    = ZIMG_ERROR_UNSUPPORTED_OPERATION + 1, /**< Subsampling format not supported. */
	ZIMG_ERROR_NO_COLORSPACE_CONVERSION   = ZIMG_ERROR_UNSUPPORTED_OPERATION + 2, /**< No conversion between colorspaces. */
	ZIMG_ERROR_NO_FIELD_PARITY_CONVERSION = ZIMG_ERROR_UNSUPPORTED_OPERATION + 3, /**< No conversion between field parity. */
	ZIMG_ERROR_RESAMPLING_NOT_AVAILABLE   = ZIMG_ERROR_UNSUPPORTED_OPERATION + 4  /**< Resampling filter not available for given image size. */
} zimg_error_code_e;

/**
 * Get information regarding the last error to occur.
 *
 * The error code is stored per-thread. It is not reset when a function
 * completes successfully, but only upon calling {@link zimg_clear_last_error}.
 *
 * @see zimg_clear_last_error
 *
 * @param[out] err_msg buffer to receive the error message, may be NULL
 * @param n length of {@p err_msg} buffer in bytes
 * @return error code
 */
ZIMG_VISIBILITY
zimg_error_code_e zimg_get_last_error(char *err_msg, size_t n);

/**
 * Clear the stored error details.
 *
 * Error details from the last error to occur are stored in per-thread memory.
 * If an error occurs on a thread, and the application does not intend to make
 * further library calls, this function may be used to reclaim memory used to
 * store the error details, such as the error message.
 *
 * @see zimg_get_last_error
 *
 * @post zimg_get_last_error() == 0
 */
ZIMG_VISIBILITY
void zimg_clear_last_error(void);


/**
 * CPU feature set constants.
 *
 * Available values are defined on a per-architecture basis.
 * Constants are not implied to be in any particular order.
 */
typedef enum zimg_cpu_type_e {
	ZIMG_CPU_NONE     = 0, /**< Portable C-based implementation. */
	ZIMG_CPU_AUTO     = 1, /**< Runtime CPU detection. */
	ZIMG_CPU_AUTO_64B = 2  /**< Allow use of 64-byte (512-bit) instructions. Since API 2.3. */
#if defined(__i386) || defined(_M_IX86) || defined(_M_X64) || defined(__x86_64__)
	,ZIMG_CPU_X86_MMX       = 1000,
	ZIMG_CPU_X86_SSE        = 1001,
	ZIMG_CPU_X86_SSE2       = 1002,
	ZIMG_CPU_X86_SSE3       = 1003,
	ZIMG_CPU_X86_SSSE3      = 1004,
	ZIMG_CPU_X86_SSE41      = 1005,
	ZIMG_CPU_X86_SSE42      = 1006,
	ZIMG_CPU_X86_AVX        = 1007,
	ZIMG_CPU_X86_F16C       = 1008, /**< AVX with F16C extension (e.g. Ivy Bridge). */
	ZIMG_CPU_X86_AVX2       = 1009,
	ZIMG_CPU_X86_AVX512F    = 1010,
	ZIMG_CPU_X86_AVX512_SKX = 1011, /**< AVX-512 {F,CD,VL,BW,DQ} (e.g. Skylake-X/SP). */
	ZIMG_CPU_X86_AVX512_CLX = 1012, /**< SKX + VNNI */
	ZIMG_CPU_X86_AVX512_PMC = 1013, /**< SKX + VBMI + IFMA52 */
	ZIMG_CPU_X86_AVX512_SNC = 1014  /**< PMC + VPOPCNTDQ + BITALG + VBMI2 + VNNI */
#elif defined(__arm__) || defined(__aarch64__) || defined(_M_ARM) || defined(_M_ARM64)
    ,ZIMG_CPU_ARM_NEON_VFPv3 = 2000, /**< ARMv7-A baseline. */
    ZIMG_CPU_ARM_NEON_VFPv4  = 2001  /**< ARMv7-A with VFPv4 (e.g. Cortex-A7) or ARMv8-A. */
#endif
} zimg_cpu_type_e;

/**
 * Pixel format constants.
 *
 * The use of the {@link ZIMG_PIXEL_HALF} format is likely to be slow
 * on CPU architectures that do not support hardware binary16 operations.
 */
typedef enum zimg_pixel_type_e {
	ZIMG_PIXEL_BYTE  = 0, /**< Unsigned integer, one byte per sample. */
	ZIMG_PIXEL_WORD  = 1, /**< Unsigned integer, two bytes per sample. */
	ZIMG_PIXEL_HALF  = 2, /**< IEEE-754 half precision (binary16). */
	ZIMG_PIXEL_FLOAT = 3  /**< IEEE-754 single precision (binary32). */
} zimg_pixel_type_e;

/**
 * Pixel range constants for integer formats.
 *
 * Additional range types may be defined besides ZIMG_RANGE_LIMITED and
 * ZIMG_RANGE_FULL. Users should not treat range as a boolean quantity.
 *
 * Negative values are reserved by the library for non-ITU extensions.
 */
typedef enum zimg_pixel_range_e {
	ZIMG_RANGE_INTERNAL = -1, /**< Not part of the API. */
	ZIMG_RANGE_LIMITED  = 0,  /**< Studio (TV) legal range, 16-235 in 8 bits. */
	ZIMG_RANGE_FULL     = 1   /**< Full (PC) dynamic range, 0-255 in 8 bits. */
} zimg_pixel_range_e;

/**
 * Color family constants.
 */
typedef enum zimg_color_family_e {
	ZIMG_COLOR_GREY = 0, /**< Single image plane. */
	ZIMG_COLOR_RGB  = 1, /**< Generic RGB color image. */
	ZIMG_COLOR_YUV  = 2  /**< Generic YUV color image. */
} zimg_color_family_e;

/**
 * Alpha channel constants.
 */
typedef enum zimg_alpha_type_e {
	ZIMG_ALPHA_NONE          = 0, /**< No alpha channel. */
	ZIMG_ALPHA_STRAIGHT      = 1, /**< Straight alpha. */
	ZIMG_ALPHA_PREMULTIPLIED = 2  /**< Premultiplied alpha. */
} zimg_alpha_type_e;

/**
 * Field parity constants.
 *
 * It is possible to process interlaced images with the library by separating
 * them into their individual fields. Each field can then be resized by
 * specifying the appropriate field parity to maintain correct alignment.
 */
typedef enum zimg_field_parity_e {
	ZIMG_FIELD_PROGRESSIVE = 0, /**< Progressive scan image. */
	ZIMG_FIELD_TOP         = 1, /**< Top field of interlaced image. */
	ZIMG_FIELD_BOTTOM      = 2  /**< Bottom field of interlaced image. */
} zimg_field_parity_e;

/**
 * Chroma location constants.
 *
 * These constants mirror those defined in ITU-T H.264 and H.265.
 *
 * The ITU-T standards define these constants only for 4:2:0 subsampled
 * images, but as an extension, the library also interprets them for other
 * subsampled formats. When used with interlaced images, the field parity must
 * also be provided.
 *
 * Chroma location is always treated as centered on unsubsampled axes.
 *
 * Negative values are reserved by the library for non-ITU extensions.
 */
typedef enum zimg_chroma_location_e {
	ZIMG_CHROMA_INTERNAL    = -1, /**< Not part of the API. */
	ZIMG_CHROMA_LEFT        = 0,  /**< MPEG-2 */
	ZIMG_CHROMA_CENTER      = 1,  /**< MPEG-1/JPEG */
	ZIMG_CHROMA_TOP_LEFT    = 2,  /**< DV */
	ZIMG_CHROMA_TOP         = 3,
	ZIMG_CHROMA_BOTTOM_LEFT = 4,
	ZIMG_CHROMA_BOTTOM      = 5
} zimg_chroma_location_e;

/**
 * Colorspace definition constants.
 *
 * These constants mirror those defined in ITU-T H.264 and H.265.
 *
 * The UNSPECIFIED value is intended to allow colorspace conversions which do
 * not require a fully specified colorspace. The primaries must be defined if
 * the transfer function is defined, and the matrix coefficients must likewise
 * be defined if the transfer function is defined.
 *
 * Unenumerated values between 0 and 255, inclusive, may be specified for any
 * colorspace parameter. In such a case, no conversion will be possible unless
 * the input and output spaces are exactly equivalent.
 *
 * Negative values are reserved by the library for non-ITU extensions.
 */
typedef enum zimg_matrix_coefficients_e {
	ZIMG_MATRIX_INTERNAL                 = -1, /**< Not part of the API. */
	ZIMG_MATRIX_RGB                      = 0,
	ZIMG_MATRIX_BT709                    = 1,
	ZIMG_MATRIX_UNSPECIFIED              = 2,
	ZIMG_MATRIX_FCC                      = 4,
	ZIMG_MATRIX_BT470_BG                 = 5,
	ZIMG_MATRIX_ST170_M                  = 6,  /* Equivalent to 5. */
	ZIMG_MATRIX_ST240_M                  = 7,
	ZIMG_MATRIX_YCGCO                    = 8,
	ZIMG_MATRIX_BT2020_NCL               = 9,
	ZIMG_MATRIX_BT2020_CL                = 10,
	ZIMG_MATRIX_CHROMATICITY_DERIVED_NCL = 12, /* Requires primaries to be set. */
	ZIMG_MATRIX_CHROMATICITY_DERIVED_CL  = 13, /* Requires primaries to be set. */
	ZIMG_MATRIX_ICTCP                    = 14
#define ZIMG_MATRIX_709      ZIMG_MATRIX_BT709      /**< Deprecated. */
#define ZIMG_MATRIX_470BG    ZIMG_MATRIX_BT470_BG   /**< Deprecated. */
#define ZIMG_MATRIX_170M     ZIMG_MATRIX_ST170_M    /**< Deprecated. */
#define ZIMG_MATRIX_240M     ZIMG_MATRIX_ST240_M    /**< Deprecated. */
#define ZIMG_MATRIX_2020_NCL ZIMG_MATRIX_BT2020_NCL /**< Deprecated. */
#define ZIMG_MATRIX_2020_CL  ZIMG_MATRIX_BT2020_CL  /**< Deprecated. */
} zimg_matrix_coefficients_e;

typedef enum zimg_transfer_characteristics_e {
	ZIMG_TRANSFER_INTERNAL      = -1, /**< Not part of the API. */
	ZIMG_TRANSFER_BT709         = 1,
	ZIMG_TRANSFER_UNSPECIFIED   = 2,
	ZIMG_TRANSFER_BT470_M       = 4,
	ZIMG_TRANSFER_BT470_BG      = 5,
	ZIMG_TRANSFER_BT601         = 6,  /* Equivalent to 1. */
	ZIMG_TRANSFER_ST240_M       = 7,
	ZIMG_TRANSFER_LINEAR        = 8,
	ZIMG_TRANSFER_LOG_100       = 9,
	ZIMG_TRANSFER_LOG_316       = 10,
	ZIMG_TRANSFER_IEC_61966_2_4 = 11,
	ZIMG_TRANSFER_IEC_61966_2_1 = 13,
	ZIMG_TRANSFER_BT2020_10     = 14, /* Equivalent to 1. */
	ZIMG_TRANSFER_BT2020_12     = 15, /* Equivalent to 1. */
	ZIMG_TRANSFER_ST2084        = 16,
	ZIMG_TRANSFER_ST428         = 17,
	ZIMG_TRANSFER_ARIB_B67      = 18
#define ZIMG_TRANSFER_709     ZIMG_TRANSFER_BT709     /**< Deprecated. */
#define ZIMG_TRANSFER_470_M   ZIMG_TRANSFER_BT470_M   /**< Deprecated. */
#define ZIMG_TRANSFER_470_BG  ZIMG_TRANSFER_BT470_BG  /**< Deprecated. */
#define ZIMG_TRANSFER_601     ZIMG_TRANSFER_BT601     /**< Deprecated. */
#define ZIMG_TRANSFER_240M    ZIMG_TRANSFER_ST240_M   /**< Deprecated. */
#define ZIMG_TRANSFER_2020_10 ZIMG_TRANSFER_BT2020_10 /**< Deprecated. */
#define ZIMG_TRANSFER_2020_12 ZIMG_TRANSFER_BT2020_12 /**< Deprecated. */
} zimg_transfer_characteristics_e;

typedef enum zimg_color_primaries_e {
	ZIMG_PRIMARIES_INTERNAL    = -1, /**< Not part of the API. */
	ZIMG_PRIMARIES_BT709       = 1,
	ZIMG_PRIMARIES_UNSPECIFIED = 2,
	ZIMG_PRIMARIES_BT470_M     = 4,
	ZIMG_PRIMARIES_BT470_BG    = 5,
	ZIMG_PRIMARIES_ST170_M     = 6,
	ZIMG_PRIMARIES_ST240_M     = 7,  /* Equivalent to 6. */
	ZIMG_PRIMARIES_FILM        = 8,
	ZIMG_PRIMARIES_BT2020      = 9,
	ZIMG_PRIMARIES_ST428       = 10,
	ZIMG_PRIMARIES_ST431_2     = 11,
	ZIMG_PRIMARIES_ST432_1     = 12,
	ZIMG_PRIMARIES_EBU3213_E   = 22
#define ZIMG_PRIMARIES_709    ZIMG_PRIMARIES_BT709    /**< Deprecated. */
#define ZIMG_PRIMARIES_470_M  ZIMG_PRIMARIES_BT470_M  /**< Deprecated. */
#define ZIMG_PRIMARIES_470_BG ZIMG_PRIMARIES_BT470_BG /**< Deprecated. */
#define ZIMG_PRIMARIES_170M   ZIMG_PRIMARIES_ST170_M  /**< Deprecated. */
#define ZIMG_PRIMARIES_240M   ZIMG_PRIMARIES_ST240_M  /**< Deprecated. */
#define ZIMG_PRIMARIES_2020   ZIMG_PRIMARIES_BT2020   /**< Deprecated. */
} zimg_color_primaries_e;

/**
 * Dither method constants.
 */
typedef enum zimg_dither_type_e {
	ZIMG_DITHER_NONE            = 0, /**< Round to nearest. */
	ZIMG_DITHER_ORDERED         = 1, /**< Bayer patterned dither. */
	ZIMG_DITHER_RANDOM          = 2, /**< Pseudo-random noise of magnitude 0.5. */
	ZIMG_DITHER_ERROR_DIFFUSION = 3  /**< Floyd-Steinberg error diffusion. */
} zimg_dither_type_e;

/**
 * Resampling method constants.
 */
typedef enum zimg_resample_filter_e {
	ZIMG_RESIZE_POINT    = 0, /**< Nearest-neighbor filter, never anti-aliased. */
	ZIMG_RESIZE_BILINEAR = 1, /**< Bilinear interpolation. */
	ZIMG_RESIZE_BICUBIC  = 2, /**< Bicubic convolution (separable) filter. */
	ZIMG_RESIZE_SPLINE16 = 3, /**< "Spline16" filter from AviSynth. */
	ZIMG_RESIZE_SPLINE36 = 4, /**< "Spline36" filter from AviSynth. */
	ZIMG_RESIZE_SPLINE64 = 6, /**< "Spline64" filter from AviSynth. */
	ZIMG_RESIZE_LANCZOS  = 5  /**< Lanczos resampling filter with variable number of taps. */
} zimg_resample_filter_e;


#define ZIMG_BUFFER_MAX ((unsigned)-1)

 /**
  * Read-only buffer structure.
  *
  * Image data is read and written from a circular array described by
  * this structure. This structure is used for input parameters, and the
  * {@link zimg_image_buffer} structure for output parameters.
  *
  * The circular array holds a power-of-2 number of image scanlines,
  * where the beginning of the i-th row of the p-th plane is stored at
  * (plane[p].data + (ptrdiff_t)(i & plane[p].mask) * plane[p].stride).
  * The plane order is R-G-B-A, Y-U-V-A, or X-Y-Z-A. If present, an alpha
  * channel is always the fourth plane, even if the image is greyscale.
  *
  * The row index mask can be set to the special value of
  * {@link ZIMG_BUFFER_MAX} to indicate a fully allocated image plane. Filter
  * instances will not read or write beyond image bounds, and no padding is
  * necessary.
  *
  * The image address and stride must be a multiple of the alignment imposed
  * by the host CPU architecture. On x86 and AMD64, this is 32 bytes. When
  * operating in 64-byte mode ({@link ZIMG_CPU_AUTO_64B}), the alignment
  * requirement is increased to 64 bytes. The stride may be negative.
  */
typedef struct zimg_image_buffer_const {
	unsigned version; /**< @see ZIMG_API_VERSION */

	struct {
		const void *data; /**< Plane data buffer */
		ptrdiff_t stride; /**< Plane stride in bytes */
		unsigned mask;    /**< Plane row index mask */
	} plane[4];
} zimg_image_buffer_const;

/**
 * Writable buffer structure.
 *
 * @see zimg_image_buffer_const
 */
typedef struct zimg_image_buffer {
	unsigned version; /**< @see ZIMG_API_VERSION */

	struct {
		void *data;       /**< Plane data buffer */
		ptrdiff_t stride; /**< Plane stride in bytes */
		unsigned mask;    /**< Plane row index mask */
	} plane[4];
} zimg_image_buffer;

/**
 * Convert a number of lines to a {@link zimg_image_buffer} mask.
 *
 * @param count number of lines, can be {@link ZIMG_BUFFER_MAX}
 * @return buffer mask, can be {@link ZIMG_BUFFER_MAX}
 */
ZIMG_VISIBILITY
unsigned zimg_select_buffer_mask(unsigned count);


/**
 * Handle to an image processing context.
 *
 * The filter graph constitutes a series of indivdual image manipulations
 * that are executed in sequence to convert an image between formats.
 *
 * A format is defined as the set of attributes that uniquely define the
 * memory representation and interpretation of an image, including its
 * resolution, colorspace, chroma format, and storage.
 */
typedef struct zimg_filter_graph zimg_filter_graph;

/**
 * User callback for custom input/output.
 *
 * The filter graph can be used either to process an in-memory planar image,
 * as defined by a {@link zimg_image_buffer} with a mask of
 * {@link ZIMG_BUFFER_MAX}, or to process images stored in arbitrary packed
 * formats or other address spaces.
 *
 * If provided to {@link zimg_filter_graph_process}, the callback will be
 * called before image data is read from the input buffer and after data is
 * written to the output buffer. The callback may be invoked on the same pixels
 * multiple times, in which case those pixels must be re-read unless the buffer
 * mask is {@link ZIMG_BUFFER_MAX}.
 *
 * If the image is subsampled, a number of scanlines in units of the chroma
 * subsampling (e.g. 2 lines for 4:2:0) must be read.
 *
 * If the callback fails, processing will be aborted and a non-zero value will
 * be returned to the caller of {@link zimg_filter_graph_process}, but the
 * return code of the callback will not be propagated.
 *
 * @param user user-defined private data
 * @param i index of first line to read/write
 * @param left index of left column in line
 * @param right index of right column in line plus one
 * @return zero on success or non-zero on failure
 */
typedef int (*zimg_filter_graph_callback)(void *user, unsigned i, unsigned left, unsigned right);

/**
 * Delete the filter graph.
 *
 * @param ptr graph handle, may be NULL
 */
ZIMG_VISIBILITY
void zimg_filter_graph_free(zimg_filter_graph *ptr);

/**
 * Query the size of the temporary buffer required to execute the graph.
 *
 * The filter graph does not allocate memory during processing and generally
 * will not fail unless a user-provided callback fails. To facilitate this,
 * memory allocation is delegated to the caller.
 *
 * @pre out != 0
 * @param ptr graph handle
 * @param[out] out set to the size of the buffer in bytes
 * @return error code
 */
ZIMG_VISIBILITY
zimg_error_code_e zimg_filter_graph_get_tmp_size(const zimg_filter_graph *ptr, size_t *out);

/**
 * Query the minimum number of lines required in the input buffer.
 *
 * When reading an image through a user-defined callback function, the loaded
 * image data is stored in a buffer of sufficient size for the granularity of
 * the image filters used.
 *
 * @pre out != 0
 * @param ptr graph handle
 * @param[out] out set to the number of scanlines
 * @return error code
 */
ZIMG_VISIBILITY
zimg_error_code_e zimg_filter_graph_get_input_buffering(const zimg_filter_graph *ptr, unsigned *out);

/**
 * Query the minimum number of lines required in the output buffer.
 *
 * @pre out != 0
 * @param ptr graph handle
 * @param[out] out set to the number of scanlines
 * @return error code
 * @see zimg2_filter_graph_get_input_buffering
 */
ZIMG_VISIBILITY
zimg_error_code_e zimg_filter_graph_get_output_buffering(const zimg_filter_graph *ptr, unsigned *out);

/**
 * Process an image with the filter graph.
 *
 * @param ptr graph handle
 * @param[in] src input image buffer
 * @param[out] dst output image buffer
 * @param tmp temporary buffer
 * @param unpack_cb user-defined input callback, may be NULL
 * @param unpack_user private data for callback
 * @param pack_cb user-defined output callback, may be NULL
 * @param pack_user private data for callback
 * @return error code
 */
ZIMG_VISIBILITY
zimg_error_code_e zimg_filter_graph_process(const zimg_filter_graph *ptr, const zimg_image_buffer_const *src, const zimg_image_buffer *dst, void *tmp,
                                            zimg_filter_graph_callback unpack_cb, void *unpack_user,
                                            zimg_filter_graph_callback pack_cb, void *pack_user);


/**
 * Image format descriptor.
 */
typedef struct zimg_image_format {
	unsigned version; /**< @see ZIMG_API_VERSION */

	unsigned width;                                           /**< Image width (required). */
	unsigned height;                                          /**< Image height (required). */
	zimg_pixel_type_e pixel_type;                             /**< Pixel type (required). */

	unsigned subsample_w;                                     /**< Horizontal subsampling factor log2 (default 0). */
	unsigned subsample_h;                                     /**< Vertical subsampling factor log2 (default 0). */

	zimg_color_family_e color_family;                         /**< Color family (default ZIMG_COLOR_GREY). */
	zimg_matrix_coefficients_e matrix_coefficients;           /**< YUV transform matrix (default ZIMG_MATRIX_UNSPECIFIED). */
	zimg_transfer_characteristics_e transfer_characteristics; /**< Transfer characteristics (default ZIMG_TRANSFER_UNSPECIFIED). */
	zimg_color_primaries_e color_primaries;                   /**< Color primaries (default ZIMG_PRIMARIES_UNSPECIFIED). */

	unsigned depth;                                           /**< Bit depth (default 8 bits per byte). */
	zimg_pixel_range_e pixel_range;                           /**< Pixel range. Required for integer formats. */

	zimg_field_parity_e field_parity;                         /**< Field parity (default ZIMG_FIELD_PROGRESSIVE). */
	zimg_chroma_location_e chroma_location;                   /**< Chroma location (default ZIMG_CHROMA_LEFT). */

	/** Active image subrectangle. Since API 2.1. */
	struct {
		double left;   /**< Subpixel index of left image boundary (default NAN, treated as 0). */
		double top;    /**< Subpixel index of top image boundary (default NAN, treated as 0). */
		double width;  /**< Subpixel width, counting from {@link left} (default NAN, same as image width). */
		double height; /**< Subpixel height, counting from {@link top} (default NAN, same as image height). */
	} active_region;

	zimg_alpha_type_e alpha;                                  /**< Alpha channel (default ZIMG_ALPHA_NONE). Since API 2.4. */
} zimg_image_format;

/**
 * Graph construction parameters.
 */
typedef struct zimg_graph_builder_params {
	unsigned version; /**< @see ZIMG_API_VERSION */

	/** Luma resampling filter (default ZIMG_RESIZE_BICUBIC). */
	zimg_resample_filter_e resample_filter;

	/**
	 * Parameters for resampling filter.
	 *
	 * The meaning of this field depends on the filter selected.
	 *
	 * For ZIMG_RESIZE_BICUBIC, {@p filter_param_a} and {@p filter_param_b} are
	 * the "b" and "c" parameters. If one parameter is specified, the other must
	 * also be specified to avoid unexpected behavior.
	 *
	 * For ZIMG_RESIZE_LANCZOS, {@p filter_param_a} is the number of filter taps.
	 *
	 * The default value is NAN, which results in a library default being used.
	 */
	double filter_param_a;
	double filter_param_b;                     /**< @see filter_param_a */

	zimg_resample_filter_e resample_filter_uv; /**< Chroma resampling filter (default ZIMG_RESIZE_BILINEAR) */
	double filter_param_a_uv;                  /**< @see filter_param_a */
	double filter_param_b_uv;                  /**< @see filter_param_a */

	zimg_dither_type_e dither_type;            /**< Dithering method (default ZIMG_DITHER_NONE). */
	zimg_cpu_type_e cpu_type;                  /**< Target CPU architecture (default ZIMG_CPU_AUTO). */

	/**
	 * Nominal peak luminance (cd/m^2) for standard-dynamic range (SDR) systems.
	 *
	 * When a high dynamic range (HDR) transfer function is converted to linear
	 * light, the linear values are scaled such that nominal white (L = 1.0)
	 * matches the nominal SDR luminance. The HDR component of the signal is
	 * represented as multiples of the SDR luminance (L > 1.0).
	 *
	 * Certain HDR transfer functions (e.g. ST.2084) have a defined mapping
	 * between code values and physical luminance. When converting between
	 * absolute and relative transfer functions, the nominal peak luminance is
	 * used to scale the dequantized linear light values.
	 *
	 * Since API 2.2.
	 *
	 * The default value is NAN, which is interpreted as 100 cd/m^2.
	 */
	double nominal_peak_luminance;

	/** Allow evaluating transfer functions at reduced precision (default false). */
	char allow_approximate_gamma;
} zimg_graph_builder_params;

/**
 * Initialize image format structure with default values.
 *
 * @param[out] ptr structure to be initialized
 * @param version API version used by caller
 */
ZIMG_VISIBILITY
void zimg_image_format_default(zimg_image_format *ptr, unsigned version);

/**
 * Initialize parameters structure with default values.
 *
 * @param[out] ptr structure to be initialized
 * @param version API version used by caller
 */
ZIMG_VISIBILITY
void zimg_graph_builder_params_default(zimg_graph_builder_params *ptr, unsigned version);

/**
 * Create a graph converting the specified formats.
 *
 * Upon failure, a NULL pointer is returned. The function
 * {@link zimg_get_last_error} may be called to obtain the failure reason.
 *
 * @param[in] src_format input image format
 * @param[in] dst_format output image format
 * @param[in] params filter parameters, may be NULL
 * @return graph handle, or NULL on failure
 */
ZIMG_VISIBILITY
zimg_filter_graph *zimg_filter_graph_build(const zimg_image_format *src_format, const zimg_image_format *dst_format, const zimg_graph_builder_params *params);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* ZIMG_H_ */
